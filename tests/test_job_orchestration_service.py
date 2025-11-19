import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Adjust path to import from parent directories
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.job_orchestration_service.main import app
from backend.job_orchestration_service.database import Base, get_db
from backend.job_orchestration_service.models import Job, JobStatusLog
from backend.job_orchestration_service.schemas import User, PinnTrainingConfig, NetworkArchitecture, TrainingParameters, PhysicsLossConfig, DatasetReference
from backend.job_orchestration_service.security import get_current_active_user
from backend.job_orchestration_service.config import settings

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}, 
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(name="db_session")
def db_session_fixture():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(name="client")
def client_fixture(db_session: MagicMock):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

@pytest.fixture
def mock_current_user():
    user = User(id=1, email="test@example.com", is_active=True, roles=[], token="mock_jwt_token")
    app.dependency_overrides[get_current_active_user] = lambda: user
    return user

@pytest.fixture
def pinn_config_data():
    return {
        "output_name": "test_pinn_run",
        "network_architecture": {"layers": [50, 50], "activation": "tanh", "output_dim": 1},
        "training_parameters": {"optimizer": "Adam", "learning_rate": 0.001, "epochs": 10, "loss_weights": {}, "batch_size": 32},
        "physics_loss_config": {
            "pde_equation": "du/dt + u*du/dx = 0",
            "independent_variables": ["x", "t"],
            "dependent_variables": ["u"],
            "domain_bounds": {"x": [0.0, 1.0], "t": [0.0, 1.0]},
            "num_domain_points": 100,
            "num_boundary_points": 10,
            "num_initial_points": 10
        },
        "dataset_ref": {"dataset_id": 123, "input_dataset_name": "x_data", "output_dataset_name": "y_data"}
    }

@patch('backend.job_orchestration_service.routers.jobs.job_queue.enqueue')
def test_submit_pinn_training_job(mock_enqueue, client, db_session, mock_current_user, pinn_config_data):
    mock_enqueue.return_value = MagicMock(id="rq_job_123")

    response = client.post(
        "/jobs/pinn-training",
        json=pinn_config_data,
        headers={"Authorization": "Bearer mock_jwt_token"}
    )

    assert response.status_code == 202
    job_response = response.json()
    assert job_response["job_type"] == "pinn_training"
    assert job_response["owner_id"] == mock_current_user.id
    assert job_response["status"] == "PENDING"
    assert job_response["rq_job_id"] == "rq_job_123" # CQ-JOS-002: Check rq_job_id

    mock_enqueue.assert_called_once()
    args, kwargs = mock_enqueue.call_args
    assert args[0] == 'backend.pinn_training_service.worker_task.run_pinn_training_job'
    assert kwargs['job_id'] == job_response['id']
    assert kwargs['user_id'] == mock_current_user.id
    assert kwargs['dms_token'] == mock_current_user.token # SEC-PTS-001: Check token is passed

    # Verify job and status log in DB
    db_job = db_session.query(Job).filter(Job.id == job_response['id']).first()
    assert db_job is not None
    assert db_job.rq_job_id == "rq_job_123"
    assert db_job.status == "PENDING"
    assert len(db_job.status_logs) == 1
    assert db_job.status_logs[0].status == "PENDING"

def test_get_job_status(client, db_session, mock_current_user, pinn_config_data):
    # Create a job directly in the DB for testing retrieval
    job_create_schema = PinnTrainingConfig(**pinn_config_data)
    db_job = Job(
        owner_id=mock_current_user.id,
        job_type="pinn_training",
        config=job_create_schema.model_dump(mode='json'),
        status="RUNNING",
        progress=50,
        rq_job_id="rq_job_456"
    )
    db_session.add(db_job)
    db_session.commit()
    db_session.refresh(db_job)

    response = client.get(
        f"/jobs/{db_job.id}",
        headers={"Authorization": "Bearer mock_jwt_token"}
    )

    assert response.status_code == 200
    job_response = response.json()
    assert job_response["id"] == db_job.id
    assert job_response["status"] == "RUNNING"
    assert job_response["rq_job_id"] == "rq_job_456"

def test_get_job_status_not_found(client, mock_current_user):
    response = client.get(
        "/jobs/999",
        headers={"Authorization": "Bearer mock_jwt_token"}
    )
    assert response.status_code == 404

def test_get_job_status_unauthorized(client, db_session, mock_current_user, pinn_config_data):
    # Create a job owned by a different user
    job_create_schema = PinnTrainingConfig(**pinn_config_data)
    db_job = Job(
        owner_id=mock_current_user.id + 1,
        job_type="pinn_training",
        config=job_create_schema.model_dump(mode='json'),
        status="PENDING"
    )
    db_session.add(db_job)
    db_session.commit()
    db_session.refresh(db_job)

    response = client.get(
        f"/jobs/{db_job.id}",
        headers={"Authorization": "Bearer mock_jwt_token"}
    )
    assert response.status_code == 403

@patch('backend.job_orchestration_service.storage_utils.get_object_content_from_minio', new_callable=AsyncMock)
def test_get_job_logs(mock_get_object_content, client, db_session, mock_current_user, pinn_config_data):
    # Create a job with a logs_path
    job_create_schema = PinnTrainingConfig(**pinn_config_data)
    db_job = Job(
        owner_id=mock_current_user.id,
        job_type="pinn_training",
        config=job_create_schema.model_dump(mode='json'),
        status="COMPLETED",
        logs_path="/pinn-training-results/logs/1/test_logs.txt"
    )
    db_session.add(db_job)
    db_session.commit()
    db_session.refresh(db_job)

    mock_get_object_content.return_value = "Log line 1\nLog line 2\nLog line 3"

    response = client.get(
        f"/jobs/{db_job.id}/logs",
        headers={"Authorization": "Bearer mock_jwt_token"}
    )

    assert response.status_code == 200
    log_response = response.json()
    assert log_response["message"] == "Logs retrieved successfully."
    assert log_response["logs"] == ["Log line 1", "Log line 2", "Log line 3"]
    mock_get_object_content.assert_called_once_with(db_job.logs_path)

@patch('backend.job_orchestration_service.storage_utils.get_object_content_from_minio', new_callable=AsyncMock)
def test_get_job_logs_no_path(mock_get_object_content, client, db_session, mock_current_user, pinn_config_data):
    # Create a job without a logs_path
    job_create_schema = PinnTrainingConfig(**pinn_config_data)
    db_job = Job(
        owner_id=mock_current_user.id,
        job_type="pinn_training",
        config=job_create_schema.model_dump(mode='json'),
        status="RUNNING",
        logs_path=None
    )
    db_session.add(db_job)
    db_session.commit()
    db_session.refresh(db_job)

    response = client.get(
        f"/jobs/{db_job.id}/logs",
        headers={"Authorization": "Bearer mock_jwt_token"}
    )

    assert response.status_code == 200
    log_response = response.json()
    assert log_response["message"] == "No logs available yet or logs not stored."
    assert log_response["logs"] == []
    mock_get_object_content.assert_not_called()

@patch('backend.job_orchestration_service.storage_utils.get_object_content_from_minio', new_callable=AsyncMock)
def test_get_job_logs_minio_error(mock_get_object_content, client, db_session, mock_current_user, pinn_config_data):
    # Create a job with a logs_path
    job_create_schema = PinnTrainingConfig(**pinn_config_data)
    db_job = Job(
        owner_id=mock_current_user.id,
        job_type="pinn_training",
        config=job_create_schema.model_dump(mode='json'),
        status="COMPLETED",
        logs_path="/pinn-training-results/logs/1/test_logs.txt"
    )
    db_session.add(db_job)
    db_session.commit()
    db_session.refresh(db_job)

    mock_get_object_content.side_effect = Exception("MinIO connection error")

    response = client.get(
        f"/jobs/{db_job.id}/logs",
        headers={"Authorization": "Bearer mock_jwt_token"}
    )

    assert response.status_code == 500
    assert "MinIO connection error" in response.json()["detail"]
    mock_get_object_content.assert_called_once_with(db_job.logs_path)
