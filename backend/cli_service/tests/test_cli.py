import pytest
import typer
from typer.testing import CliRunner
import respx
from httpx import Response, Request
from pathlib import Path
import json
import os
from unittest.mock import patch

# Import the CLI app and config/utils functions
from backend.cli_service.main import app
from backend.cli_service.config import save_token, load_token, delete_token, get_token_file_path
from backend.cli_service.utils import get_authenticated_client, handle_response_errors

runner = CliRunner()

# Mock settings for consistent testing
@pytest.fixture(autouse=True)
def mock_settings():
    with patch('backend.cli_service.config.settings') as mock_config:
        mock_config.AUTH_SERVICE_URL = "http://mock-auth"
        mock_config.DATA_MANAGEMENT_SERVICE_URL = "http://mock-data"
        mock_config.JOB_ORCHESTRATION_SERVICE_URL = "http://mock-job"
        mock_config.CLI_CONFIG_DIR = Path("/tmp/pinn_cli_test")
        mock_config.CLI_TOKEN_FILE = mock_config.CLI_CONFIG_DIR / "token.yaml"
        yield mock_config
    # Clean up after tests
    if mock_config.CLI_CONFIG_DIR.exists():
        import shutil
        shutil.rmtree(mock_config.CLI_CONFIG_DIR)

@pytest.fixture
def temp_token_file(mock_settings):
    # Ensure the directory exists for the test
    mock_settings.CLI_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    yield mock_settings.CLI_TOKEN_FILE
    # Clean up
    if mock_settings.CLI_TOKEN_FILE.exists():
        os.remove(mock_settings.CLI_TOKEN_FILE)

# --- Test config.py functions ---
def test_save_and_load_token(temp_token_file):
    test_token = "test_jwt_token"
    save_token(test_token)
    assert temp_token_file.exists()
    loaded_token = load_token()
    assert loaded_token == test_token

def test_load_token_no_file(temp_token_file):
    if temp_token_file.exists():
        os.remove(temp_token_file)
    assert load_token() is None

def test_delete_token(temp_token_file):
    test_token = "test_jwt_token"
    save_token(test_token)
    assert temp_token_file.exists()
    delete_token()
    assert not temp_token_file.exists()

# --- Test utils.py functions ---
def test_get_authenticated_client_success(temp_token_file):
    save_token("mock_token")
    client = get_authenticated_client()
    assert client.headers["Authorization"] == "Bearer mock_token"

def test_get_authenticated_client_no_token():
    with pytest.raises(typer.Exit) as exc_info:
        get_authenticated_client()
    assert exc_info.value.code == 1

def test_handle_response_errors_no_error():
    response = Response(200, request=Request("GET", "http://test.com"))
    handle_response_errors(response) # Should not raise

def test_handle_response_errors_with_error():
    response = Response(400, request=Request("GET", "http://test.com"), json={"detail": "Bad Request"})
    with pytest.raises(respx.HTTPStatusError):
        handle_response_errors(response)

# --- Test auth_cli.py commands ---
@respx.mock
def test_register_success(mock_settings):
    respx.post(f"{mock_settings.AUTH_SERVICE_URL}/auth/register").return_value = Response(
        200, json={"id": 1, "email": "test@example.com"}
    )
    result = runner.invoke(app, ["auth", "register", "-e", "test@example.com", "-p", "password123"], input="password123\n")
    assert result.exit_code == 0
    assert "User 'test@example.com' registered successfully" in result.stdout

@respx.mock
def test_register_failure(mock_settings):
    respx.post(f"{mock_settings.AUTH_SERVICE_URL}/auth/register").return_value = Response(
        400, json={"detail": "User already exists"}
    )
    result = runner.invoke(app, ["auth", "register", "-e", "test@example.com", "-p", "password123"], input="password123\n")
    assert result.exit_code == 0 # Typer catches exceptions and prints, doesn't exit with error code
    assert "Registration failed: User already exists" in result.stdout

@respx.mock
def test_login_success(mock_settings, temp_token_file):
    respx.post(f"{mock_settings.AUTH_SERVICE_URL}/auth/login").return_value = Response(
        200, json={"access_token": "mock_jwt_token", "token_type": "bearer"}
    )
    result = runner.invoke(app, ["auth", "login", "-e", "test@example.com", "-p", "password123"])
    assert result.exit_code == 0
    assert "Login successful. Token saved." in result.stdout
    assert load_token() == "mock_jwt_token"

@respx.mock
def test_login_failure(mock_settings, temp_token_file):
    respx.post(f"{mock_settings.AUTH_SERVICE_URL}/auth/login").return_value = Response(
        401, json={"detail": "Invalid credentials"}
    )
    result = runner.invoke(app, ["auth", "login", "-e", "test@example.com", "-p", "wrongpassword"])
    assert result.exit_code == 0
    assert "Login failed: Invalid credentials" in result.stdout
    assert load_token() is None

def test_logout_success(temp_token_file):
    save_token("mock_jwt_token")
    result = runner.invoke(app, ["auth", "logout"])
    assert result.exit_code == 0
    assert "Logged out. Token cleared." in result.stdout
    assert load_token() is None

@respx.mock
def test_whoami_success(mock_settings, temp_token_file):
    save_token("mock_jwt_token")
    respx.get(f"{mock_settings.AUTH_SERVICE_URL}/auth/me").return_value = Response(
        200, json={"id": 1, "email": "test@example.com", "is_active": True, "roles": [{"name": "user"}]}
    )
    result = runner.invoke(app, ["auth", "whoami"])
    assert result.exit_code == 0
    assert "You are logged in as:" in result.stdout
    assert "Email: test@example.com" in result.stdout

@respx.mock
def test_whoami_not_logged_in(mock_settings):
    # Ensure no token is saved
    if get_token_file_path().exists():
        delete_token()
    result = runner.invoke(app, ["auth", "whoami"])
    assert result.exit_code == 1 # Exits with error code 1 due to typer.Exit
    assert "Error: Not logged in." in result.stdout

# --- Test dataset_cli.py commands ---
@respx.mock
def test_list_datasets_success(mock_settings, temp_token_file):
    save_token("mock_jwt_token")
    respx.get(f"{mock_settings.DATA_MANAGEMENT_SERVICE_URL}/datasets/").return_value = Response(
        200, json=[
            {"id": 1, "name": "dataset1", "description": "Desc1", "owner_id": 1, "latest_version": {"id": 101, "version_number": 1, "uploaded_at": "2023-01-01T10:00:00Z", "storage_path": "/path/to/ds1"}},
            {"id": 2, "name": "dataset2", "description": None, "owner_id": 1, "latest_version": {"id": 102, "version_number": 1, "uploaded_at": "2023-01-02T11:00:00Z", "storage_path": "/path/to/ds2"}}
        ]
    )
    result = runner.invoke(app, ["datasets", "list"])
    assert result.exit_code == 0
    assert "Your Datasets" in result.stdout
    assert "dataset1" in result.stdout
    assert "dataset2" in result.stdout

@respx.mock
def test_upload_dataset_success(mock_settings, temp_token_file, tmp_path):
    save_token("mock_jwt_token")
    test_file = tmp_path / "test_data.csv"
    test_file.write_text("col1,col2\n1,2")

    respx.post(f"{mock_settings.DATA_MANAGEMENT_SERVICE_URL}/datasets/").return_value = Response(
        200, json={"id": 1, "name": "new_dataset", "latest_version": {"id": 101, "storage_path": "/path/to/new_ds"}}
    )
    result = runner.invoke(app, ["datasets", "upload", str(test_file), "--name", "new_dataset", "--description", "A new dataset"])
    assert result.exit_code == 0
    assert "Dataset 'new_dataset' (ID: 1) uploaded successfully!" in result.stdout

@respx.mock
def test_download_dataset_success(mock_settings, temp_token_file, tmp_path):
    save_token("mock_jwt_token")
    output_file = tmp_path / "downloaded_data.csv"
    
    respx.get(f"{mock_settings.DATA_MANAGEMENT_SERVICE_URL}/datasets/1/download_link").return_value = Response(
        200, json={"download_url": "http://mock-storage/data.csv"}
    )
    respx.get("http://mock-storage/data.csv").return_value = Response(
        200, content=b"downloaded,content"
    )

    result = runner.invoke(app, ["datasets", "download", "1", "--output", str(output_file)])
    assert result.exit_code == 0
    assert "Dataset ID 1 downloaded successfully" in result.stdout
    assert output_file.read_text() == "downloaded,content"

# --- Test job_cli.py commands ---
@respx.mock
def test_list_jobs_success(mock_settings, temp_token_file):
    save_token("mock_jwt_token")
    respx.get(f"{mock_settings.JOB_ORCHESTRATION_SERVICE_URL}/jobs/").return_value = Response(
        200, json=[
            {"id": 1, "job_type": "pinn_training", "status": "COMPLETED", "progress": 100, "created_at": "2023-01-01T10:00:00Z", "completed_at": "2023-01-01T11:00:00Z", "error_message": None},
            {"id": 2, "job_type": "pde_discovery", "status": "RUNNING", "progress": 50, "created_at": "2023-01-02T10:00:00Z", "completed_at": None, "error_message": None}
        ]
    )
    result = runner.invoke(app, ["jobs", "list"])
    assert result.exit_code == 0
    assert "Your Jobs" in result.stdout
    assert "pinn_training" in result.stdout
    assert "pde_discovery" in result.stdout
    assert "COMPLETED" in result.stdout
    assert "RUNNING" in result.stdout

@respx.mock
def test_status_job_success(mock_settings, temp_token_file):
    save_token("mock_jwt_token")
    respx.get(f"{mock_settings.JOB_ORCHESTRATION_SERVICE_URL}/jobs/1").return_value = Response(
        200, json={
            "id": 1, "job_type": "pinn_training", "status": "COMPLETED", "progress": 100,
            "created_at": "2023-01-01T10:00:00Z", "started_at": "2023-01-01T10:05:00Z", "completed_at": "2023-01-01T11:00:00Z",
            "error_message": None, "results_path": "/results/1", "logs_path": "/logs/1",
            "status_logs": [{"timestamp": "2023-01-01T10:00:00Z", "status": "PENDING", "message": "Job created"}]
        }
    )
    result = runner.invoke(app, ["jobs", "status", "1"])
    assert result.exit_code == 0
    assert "Job Details (ID: 1):" in result.stdout
    assert "Status: COMPLETED" in result.stdout
    assert "Results Path: /results/1" in result.stdout

@respx.mock
def test_logs_job_success(mock_settings, temp_token_file):
    save_token("mock_jwt_token")
    respx.get(f"{mock_settings.JOB_ORCHESTRATION_SERVICE_URL}/jobs/1/logs").return_value = Response(
        200, json={"logs": ["Log line 1", "Log line 2"]}
    )
    result = runner.invoke(app, ["jobs", "logs", "1"])
    assert result.exit_code == 0
    assert "Job Logs:" in result.stdout
    assert "Log line 1" in result.stdout
    assert "Log line 2" in result.stdout

@respx.mock
def test_submit_pinn_training_job_success(mock_settings, temp_token_file, tmp_path):
    save_token("mock_jwt_token")
    config_file = tmp_path / "pinn_config.json"
    config_file.write_text(json.dumps({"model_name": "test_pinn"}))

    respx.post(f"{mock_settings.JOB_ORCHESTRATION_SERVICE_URL}/jobs/pinn-training").return_value = Response(
        200, json={"id": 1, "job_type": "pinn_training", "status": "PENDING"}
    )
    result = runner.invoke(app, ["jobs", "submit-pinn-training", str(config_file)])
    assert result.exit_code == 0
    assert "PINN Training Job submitted successfully! Job ID: 1" in result.stdout

@respx.mock
def test_submit_derivatives_job_success(mock_settings, temp_token_file, tmp_path):
    save_token("mock_jwt_token")
    config_file = tmp_path / "deriv_config.json"
    config_file.write_text(json.dumps({"output_name": "deriv_results"}))

    respx.post(f"{mock_settings.JOB_ORCHESTRATION_SERVICE_URL}/jobs/derivatives").return_value = Response(
        200, json={"id": 2, "job_type": "derivative_computation", "status": "PENDING"}
    )
    result = runner.invoke(app, ["jobs", "submit-derivatives", str(config_file)])
    assert result.exit_code == 0
    assert "Derivative Computation Job submitted successfully! Job ID: 2" in result.stdout

@respx.mock
def test_submit_pde_discovery_job_success(mock_settings, temp_token_file, tmp_path):
    save_token("mock_jwt_token")
    config_file = tmp_path / "pde_config.json"
    config_file.write_text(json.dumps({"discovery_algorithm": "SINDy"}))

    respx.post(f"{mock_settings.JOB_ORCHESTRATION_SERVICE_URL}/jobs/pde-discovery").return_value = Response(
        200, json={"id": 3, "job_type": "pde_discovery", "status": "PENDING"}
    )
    result = runner.invoke(app, ["jobs", "submit-pde-discovery", str(config_file)])
    assert result.exit_code == 0
    assert "PDE Discovery Job submitted successfully! Job ID: 3" in result.stdout
