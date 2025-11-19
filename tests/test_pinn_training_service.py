import pytest
import torch
import torch.nn as nn
from unittest.mock import MagicMock, AsyncMock, patch
import io
import h5py
import numpy as np

# Adjust path to import from parent directories
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.pinn_training_service.pinn_config import PinnTrainingConfig, NetworkArchitecture, TrainingParameters, PhysicsLossConfig, DatasetReference, Condition
from backend.pinn_training_service.pinn_model import MLP, build_model
from backend.pinn_training_service.pinn_solver import PinnSolver
from backend.pinn_training_service.storage_utils import fetch_dataset_from_dms
from backend.pinn_training_service.config import settings as pinn_settings

@pytest.fixture
def mock_pinn_config():
    return PinnTrainingConfig(
        output_name="test_pinn_run",
        network_architecture=NetworkArchitecture(layers=[50, 50], activation="tanh", output_dim=1),
        training_parameters=TrainingParameters(optimizer="Adam", learning_rate=0.001, epochs=10, batch_size=32),
        physics_loss_config=PhysicsLossConfig(
            pde_equation="du/dt + u*du/dx - (0.01/pi)*d2u/dx2 = 0",
            independent_variables=["x", "t"],
            dependent_variables=["u"],
            domain_bounds={"x": [0.0, 1.0], "t": [0.0, 1.0]},
            num_domain_points=100,
            num_boundary_points=10,
            num_initial_points=10
        ),
        dataset_ref=DatasetReference(dataset_id=1, input_dataset_name="x_data", output_dataset_name="y_data")
    )

@pytest.fixture
def mock_pinn_config_with_cross_derivative():
    return PinnTrainingConfig(
        output_name="test_pinn_run_cross",
        network_architecture=NetworkArchitecture(layers=[50, 50], activation="tanh", output_dim=1),
        training_parameters=TrainingParameters(optimizer="Adam", learning_rate=0.001, epochs=10, batch_size=32),
        physics_loss_config=PhysicsLossConfig(
            pde_equation="d2u/dxdy + du/dx = 0", # Example with cross-derivative
            independent_variables=["x", "y"],
            dependent_variables=["u"],
            domain_bounds={"x": [0.0, 1.0], "y": [0.0, 1.0]},
            num_domain_points=100,
            num_boundary_points=10,
            num_initial_points=10
        )
    )

@pytest.fixture
def mock_model():
    return MLP(input_dim=2, output_dim=1, layers=[50, 50])

def test_build_model(mock_pinn_config):
    config = mock_pinn_config.network_architecture
    model = build_model(input_dim=2, config=config)
    assert isinstance(model, MLP)
    assert len(model.net) == (len(config.layers) * 2) + 1 # 2 linear + 1 activation per layer, plus final linear
    assert model.net[0].in_features == 2
    assert model.net[-1].out_features == config.output_dim

def test_pinn_solver_init(mock_model, mock_pinn_config):
    solver = PinnSolver(mock_model, mock_pinn_config)
    assert solver.model == mock_model
    assert solver.config == mock_pinn_config
    assert solver.optimizer is not None
    assert solver.loss_fn is not None
    assert len(solver.independent_vars) == 2 # x, t
    assert len(solver.dependent_vars) == 1 # u
    assert solver.pde_expr is not None
    assert solver.pde_func is not None

def test_pinn_solver_pde_validation_rce(mock_model, mock_pinn_config):
    # SEC-JOS-001: Test RCE prevention
    malicious_pde_config = mock_pinn_config.model_copy(deep=True)
    malicious_pde_config.physics_loss_config.pde_equation = "import os; os.system('rm -rf /')" # Malicious code
    with pytest.raises(ValueError, match="forbidden keyword: 'import'"):
        PinnSolver(mock_model, malicious_pde_config)

    malicious_pde_config.physics_loss_config.pde_equation = "__import__('os').system('rm -rf /')" # Malicious code
    with pytest.raises(ValueError, match="forbidden '__' sequence"):
        PinnSolver(mock_model, malicious_pde_config)

@patch('torch.autograd.grad')
def test_pinn_solver_compute_derivatives(mock_grad, mock_model, mock_pinn_config):
    solver = PinnSolver(mock_model, mock_pinn_config)
    dummy_y = torch.randn(10, 1, requires_grad=True)
    dummy_x = torch.randn(10, 1, requires_grad=True)

    # Mock the return of torch.autograd.grad
    mock_grad.return_value = [torch.randn(10, 1)]

    # Test first order derivative
    deriv1 = solver._compute_derivatives(dummy_y, dummy_x, order=1)
    assert deriv1 is not None
    mock_grad.assert_called_once()
    mock_grad.reset_mock()

    # Test second order derivative
    mock_grad.side_effect = [[torch.randn(10, 1, requires_grad=True)], [torch.randn(10, 1)]]
    deriv2 = solver._compute_derivatives(dummy_y, dummy_x, order=2)
    assert deriv2 is not None
    assert mock_grad.call_count == 2

@patch('backend.pinn_training_service.pinn_solver.PinnSolver._compute_derivatives')
def test_pinn_solver_compute_pde_loss_cross_derivative(mock_compute_derivatives, mock_model, mock_pinn_config_with_cross_derivative):
    # CQ-PTS-001: Test cross-derivative computation in PDE loss
    solver = PinnSolver(mock_model, mock_pinn_config_with_cross_derivative)
    x_pde = torch.randn(10, 2, requires_grad=True)
    
    # Mock model output
    solver.model = MagicMock(spec=MLP)
    solver.model.return_value = torch.randn(10, 1)

    # Mock _compute_derivatives to return dummy tensors
    # This needs to be carefully ordered based on how _compute_pde_loss calls it
    # For d2u/dxdy + du/dx = 0:
    # 1. du/dx
    # 2. d(du/dx)/dy (which is d2u/dxdy)
    mock_compute_derivatives.side_effect = [
        torch.randn(10, 1), # du/dx
        torch.randn(10, 1)  # d2u/dxdy
    ]

    loss = solver._compute_pde_loss(x_pde)
    assert isinstance(loss, torch.Tensor)
    assert loss.item() >= 0
    assert mock_compute_derivatives.call_count == 2

@pytest.mark.asyncio
@patch('httpx.AsyncClient')
def test_fetch_dataset_from_dms(mock_async_client, mock_pinn_config):
    # CQ-PTS-002: Test flexible HDF5 parsing
    mock_response_download_link = MagicMock()
    mock_response_download_link.json.return_value = {"download_url": "http://mock.dms/presigned_url"}
    mock_response_download_link.raise_for_status = MagicMock()

    mock_response_data = MagicMock()
    mock_response_data.raise_for_status = MagicMock()

    # Create a dummy HDF5 file in memory
    dummy_h5_buffer = io.BytesIO()
    with h5py.File(dummy_h5_buffer, 'w') as f:
        f.create_dataset(mock_pinn_config.dataset_ref.input_dataset_name, data=np.array([[1.0, 2.0], [3.0, 4.0]]))
        f.create_dataset(mock_pinn_config.dataset_ref.output_dataset_name, data=np.array([[5.0], [6.0]]))
    dummy_h5_buffer.seek(0)
    mock_response_data.content = dummy_h5_buffer.read()

    mock_async_client.return_value.__aenter__.return_value.get.side_effect = [
        mock_response_download_link, # First call for download link
        mock_response_data           # Second call for actual data
    ]

    dataset_ref = mock_pinn_config.dataset_ref
    data = await fetch_dataset_from_dms(
        dataset_ref.dataset_id, 
        1, 
        "mock_token", 
        dataset_ref.version_id,
        input_dataset_name=dataset_ref.input_dataset_name,
        output_dataset_name=dataset_ref.output_dataset_name
    )

    assert "x" in data
    assert "y" in data
    assert torch.equal(data["x"], torch.tensor([[1.0, 2.0], [3.0, 4.0]]))
    assert torch.equal(data["y"], torch.tensor([[5.0], [6.0]]))

    # Verify httpx calls
    client_instance = mock_async_client.return_value.__aenter__.return_value
    client_instance.get.assert_any_call(
        f"{pinn_settings.DATA_MANAGEMENT_SERVICE_URL}/datasets/{dataset_ref.dataset_id}/download_link",
        headers={"Authorization": "Bearer mock_token"}
    )
    client_instance.get.assert_any_call("http://mock.dms/presigned_url")

@pytest.mark.asyncio
@patch('httpx.AsyncClient')
def test_fetch_dataset_from_dms_missing_datasets(mock_async_client, mock_pinn_config):
    mock_response_download_link = MagicMock()
    mock_response_download_link.json.return_value = {"download_url": "http://mock.dms/presigned_url"}
    mock_response_download_link.raise_for_status = MagicMock()

    mock_response_data = MagicMock()
    mock_response_data.raise_for_status = MagicMock()

    # Create a dummy HDF5 file in memory with missing datasets
    dummy_h5_buffer = io.BytesIO()
    with h5py.File(dummy_h5_buffer, 'w') as f:
        f.create_dataset("wrong_x", data=np.array([[1.0, 2.0]]))
        f.create_dataset("wrong_y", data=np.array([[5.0]]))
    dummy_h5_buffer.seek(0)
    mock_response_data.content = dummy_h5_buffer.read()

    mock_async_client.return_value.__aenter__.return_value.get.side_effect = [
        mock_response_download_link, # First call for download link
        mock_response_data           # Second call for actual data
    ]

    dataset_ref = mock_pinn_config.dataset_ref
    with pytest.raises(ValueError, match=f"HDF5 file for dataset {dataset_ref.dataset_id} must contain '{dataset_ref.input_dataset_name}' and '{dataset_ref.output_dataset_name}' datasets."):
        await fetch_dataset_from_dms(
            dataset_ref.dataset_id, 
            1, 
            "mock_token", 
            dataset_ref.version_id,
            input_dataset_name=dataset_ref.input_dataset_name,
            output_dataset_name=dataset_ref.output_dataset_name
        )
