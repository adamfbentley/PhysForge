import pytest
import numpy as np
import io
import h5py
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

# Mock settings for testing
class MockSettings:
    MINIO_ENDPOINT = "localhost:9000"
    MINIO_ACCESS_KEY = "minioadmin"
    MINIO_SECRET_KEY = "minioadmin"
    MINIO_SECURE = False
    MINIO_BUCKET_NAME = "test-bucket"
    JOB_ORCHESTRATION_DATABASE_URL = "sqlite:///./test_job_orchestration.db"

# Patch settings before importing modules that use them
with patch('backend.pde_discovery_service.config.settings', MockSettings()):
    from backend.pde_discovery_service import storage_utils
    from backend.pde_discovery_service import metrics_utils
    from backend.pde_discovery_service import symbolic_utils
    from backend.pde_discovery_service.schemas import SindyConfig, PySRConfig
    from backend.pde_discovery_service.sindy_discovery import SindyDiscoverer
    from backend.pde_discovery_service.pysr_discovery import PySRDiscoverer

# --- Test storage_utils.py ---
@pytest.mark.asyncio
@patch('minio.Minio')
async def test_get_minio_client_with_token_no_token(mock_minio_class):
    mock_client_instance = MagicMock()
    mock_minio_class.return_value = mock_client_instance
    mock_client_instance.bucket_exists.return_value = True

    client = storage_utils._get_minio_client_with_token(dms_token=None)
    mock_minio_class.assert_called_once_with(
        MockSettings.MINIO_ENDPOINT,
        access_key=MockSettings.MINIO_ACCESS_KEY,
        secret_key=MockSettings.MINIO_SECRET_KEY,
        secure=MockSettings.MINIO_SECURE
    )
    assert client == mock_client_instance

@pytest.mark.asyncio
@patch('minio.Minio')
async def test_get_minio_client_with_token_with_token(mock_minio_class):
    mock_client_instance = MagicMock()
    mock_minio_class.return_value = mock_client_instance
    mock_client_instance.bucket_exists.return_value = True
    test_token = "mock_jwt_token"

    client = storage_utils._get_minio_client_with_token(dms_token=test_token)
    mock_minio_class.assert_called_once_with(
        MockSettings.MINIO_ENDPOINT,
        secure=MockSettings.MINIO_SECURE,
        session_token=test_token
    )
    assert client == mock_client_instance

@pytest.mark.asyncio
@patch('backend.pde_discovery_service.storage_utils._get_minio_client_with_token')
async def test_upload_file_to_minio(mock_get_client):
    mock_client_instance = MagicMock()
    mock_get_client.return_value = mock_client_instance
    
    test_data = b"test content"
    file_buffer = io.BytesIO(test_data)
    object_name = "test/path/file.txt"
    file_size = len(test_data)
    content_type = "text/plain"
    dms_token = "mock_token"

    result_path = await storage_utils.upload_file_to_minio(object_name, file_buffer, file_size, content_type, dms_token)
    
    mock_get_client.assert_called_once_with(dms_token)
    mock_client_instance.put_object.assert_called_once_with(
        MockSettings.MINIO_BUCKET_NAME,
        object_name,
        file_buffer,
        file_size,
        content_type=content_type
    )
    assert result_path == f"/{MockSettings.MINIO_BUCKET_NAME}/{object_name}"

@pytest.mark.asyncio
@patch('backend.pde_discovery_service.storage_utils._get_minio_client_with_token')
async def test_load_derivative_data_from_minio(mock_get_client):
    mock_client_instance = MagicMock()
    mock_get_client.return_value = mock_client_instance
    
    # Create a dummy HDF5 file in memory
    dummy_h5_buffer = io.BytesIO()
    with h5py.File(dummy_h5_buffer, 'w') as f:
        f.create_dataset('u', data=np.array([1.0, 2.0, 3.0]))
        f.create_dataset('du_dt', data=np.array([0.1, 0.2, 0.3]))
    dummy_h5_buffer.seek(0)
    
    mock_response = MagicMock()
    mock_response.read.return_value = dummy_h5_buffer.read()
    mock_response.close.return_value = None
    mock_response.release_conn.return_value = None
    mock_client_instance.get_object.return_value = mock_response

    derivative_results_path = f"/{MockSettings.MINIO_BUCKET_NAME}/data/features.h5"
    dms_token = "mock_token"

    loaded_data = await storage_utils.load_derivative_data_from_minio(derivative_results_path, dms_token)
    
    mock_get_client.assert_called_once_with(dms_token)
    mock_client_instance.get_object.assert_called_once_with(MockSettings.MINIO_BUCKET_NAME, "data/features.h5")
    assert 'u' in loaded_data
    assert 'du_dt' in loaded_data
    assert np.array_equal(loaded_data['u'], np.array([1.0, 2.0, 3.0]))

# --- Test metrics_utils.py ---
def test_calculate_sindy_aic_bic():
    mock_model = MagicMock()
    mock_model.coefficients.return_value = np.array([[0.1, 0.0, 0.5]]) # 2 non-zero coeffs
    mock_model.predict.return_value = np.array([0.1, 0.2, 0.3])

    feature_matrix = np.array([[1,2,3],[4,5,6],[7,8,9]])
    target_derivative = np.array([0.1, 0.2, 0.3]) # Perfect fit for simplicity

    metrics = metrics_utils.calculate_sindy_aic_bic(mock_model, feature_matrix, target_derivative)
    assert metrics["aic"] == -np.inf # RSS is 0
    assert metrics["bic"] == -np.inf

    # Test with non-zero RSS
    mock_model.predict.return_value = np.array([0.15, 0.25, 0.35])
    metrics = metrics_utils.calculate_sindy_aic_bic(mock_model, feature_matrix, target_derivative)
    assert metrics["aic"] != -np.inf
    assert metrics["bic"] != -np.inf
    assert isinstance(metrics["aic"], float)
    assert isinstance(metrics["bic"], float)

def test_calculate_pysr_aic_bic():
    n_samples = 100
    rss = 0.5
    k_params = 5

    metrics = metrics_utils.calculate_pysr_aic_bic(n_samples, rss, k_params)
    assert isinstance(metrics["aic"], float)
    assert isinstance(metrics["bic"], float)
    assert metrics["aic"] == n_samples * np.log(rss / n_samples) + 2 * k_params
    assert metrics["bic"] == n_samples * np.log(rss / n_samples) + k_params * np.log(n_samples)

    # Test edge cases
    assert metrics_utils.calculate_pysr_aic_bic(10, 0, 1)["aic"] == -np.inf
    assert metrics_utils.calculate_pysr_aic_bic(10, 1, 0)["aic"] == np.inf

# --- Test symbolic_utils.py ---
def test_canonicalize_equation():
    ind_vars = ['x', 't']
    dep_var = 'u'

    # Simple equation
    eq_str = "du_dt + u*du_dx = 0"
    canonical = symbolic_utils.canonicalize_equation(eq_str, ind_vars, dep_var)
    assert canonical == "Eq(Derivative(u(t, x), t), -u(t, x)*Derivative(u(t, x), x))" or \
           canonical == "Eq(Derivative(u, t), -u*Derivative(u, x))" # Sympy might simplify symbols

    # Equation already in canonical form
    eq_str = "du_dt = u"
    canonical = symbolic_utils.canonicalize_equation(eq_str, ind_vars, dep_var)
    assert canonical == "Eq(Derivative(u(t, x), t), u(t, x))" or \
           canonical == "Eq(Derivative(u, t), u)"

    # More complex equation
    eq_str = "d2u_dx2 + du_dt - u = 0"
    canonical = symbolic_utils.canonicalize_equation(eq_str, ind_vars, dep_var)
    assert canonical == "Eq(Derivative(u(t, x), (x, 2)), -Derivative(u(t, x), t) + u(t, x))" or \
           canonical == "Eq(Derivative(u, (x, 2)), -Derivative(u, t) + u)"

    # No equation
    assert symbolic_utils.canonicalize_equation("", ind_vars, dep_var) is None
    assert symbolic_utils.canonicalize_equation("No equation found", ind_vars, dep_var) == "No equation found"

# --- Test SindyDiscoverer (basic integration test) ---
@patch('pysindy.SINDy')
@patch('pysindy.STLSQ')
@patch('backend.pde_discovery_service.metrics_utils.calculate_sindy_aic_bic')
@patch('backend.pde_discovery_service.symbolic_utils.canonicalize_equation')
def test_sindy_discoverer_discover_pde(mock_canonicalize, mock_aic_bic, mock_stslq, mock_sindy):
    mock_sindy_instance = MagicMock()
    mock_sindy.return_value = mock_sindy_instance
    mock_sindy_instance.equations.return_value = ["du_dt = 0.1*u"]
    mock_sindy_instance.predict.return_value = np.array([0.1, 0.2, 0.3])
    mock_sindy_instance.coefficients.return_value = np.array([[0.1, 0.0]])

    mock_aic_bic.return_value = {"aic": 10.0, "bic": 15.0}
    mock_canonicalize.return_value = "canonical_du_dt = 0.1*u"

    config = SindyConfig(optimizer="STLSQ", threshold=0.01)
    discoverer = SindyDiscoverer(config, ['x', 't'], 'u')

    feature_matrix = np.array([[1, 1], [2, 2], [3, 3]])
    feature_names = ['u', 'du_dx']
    target_derivative = np.array([0.1, 0.2, 0.3])

    results = discoverer.discover_pde(feature_matrix, feature_names, target_derivative)

    mock_sindy.assert_called_once()
    mock_sindy_instance.fit.assert_called_once_with(feature_matrix, x_dot=target_derivative)
    mock_aic_bic.assert_called_once()
    mock_canonicalize.assert_called_once_with("du_dt = 0.1*u", ['x', 't'], 'u')

    assert results["discovered_equation"] == "du_dt = 0.1*u"
    assert results["canonical_equation"] == "canonical_du_dt = 0.1*u"
    assert "rmse" in results["equation_metrics"]
    assert results["equation_metrics"]["aic"] == 10.0

# --- Test PySRDiscoverer (basic integration test) ---
@patch('pysr.PySRRegressor')
@patch('backend.pde_discovery_service.metrics_utils.calculate_pysr_aic_bic')
@patch('backend.pde_discovery_service.symbolic_utils.canonicalize_equation')
def test_pysr_discoverer_discover_pde(mock_canonicalize, mock_aic_bic, mock_pysr_regressor):
    mock_pysr_instance = MagicMock()
    mock_pysr_regressor.return_value = mock_pysr_instance
    
    # Mock the equations_ dataframe
    mock_pysr_instance.equations_ = MagicMock()
    mock_pysr_instance.equations_.empty = False
    mock_pysr_instance.equations_.sort_values.return_value.iloc.return_value = {
        'equation': 'du_dt = u + x',
        'loss': 0.01, # MSE
        'complexity': 3,
        'r2': 0.95,
        'weighted_avg_std': 0.005,
        'bayes_factor': 100
    }
    mock_pysr_instance.equations_.to_dict.return_value = [
        {'equation': 'du_dt = u + x', 'loss': 0.01, 'complexity': 3, 'r2': 0.95},
        {'equation': 'du_dt = u', 'loss': 0.05, 'complexity': 2, 'r2': 0.9}
    ]

    mock_aic_bic.return_value = {"aic": 5.0, "bic": 8.0}
    mock_canonicalize.return_value = "canonical_du_dt = u + x"

    config = PySRConfig(populations=10)
    discoverer = PySRDiscoverer(config, ['x', 't'], 'u')

    feature_matrix = np.array([[1, 1], [2, 2], [3, 3]])
    feature_names = ['u', 'x']
    target_derivative = np.array([2, 4, 6]) # Example target

    results = discoverer.discover_pde(feature_matrix, feature_names, target_derivative)

    mock_pysr_regressor.assert_called_once()
    mock_pysr_instance.fit.assert_called_once_with(feature_matrix, target_derivative, X_columns=feature_names)
    mock_aic_bic.assert_called_once()
    mock_canonicalize.assert_called_once_with("du_dt = u + x", ['x', 't'], 'u')

    assert results["discovered_equation"] == "du_dt = u + x"
    assert results["canonical_equation"] == "canonical_du_dt = u + x"
    assert "rmse" in results["equation_metrics"]
    assert results["equation_metrics"]["aic"] == 5.0
    assert "pysr_weighted_avg_std" in results["uncertainty_metrics"]
    assert "all_pysr_equations" in results
