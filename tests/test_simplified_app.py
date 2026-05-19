import importlib
import json
import sqlite3
from datetime import datetime

import numpy as np
import pandas as pd
import pytest
import torch
from fastapi.testclient import TestClient


@pytest.fixture()
def app_module(tmp_path, monkeypatch):
    module = importlib.import_module("app_simplified.app")

    upload_dir = tmp_path / "uploads"
    results_dir = tmp_path / "results"
    upload_dir.mkdir()
    results_dir.mkdir()

    monkeypatch.setattr(module, "DB_PATH", tmp_path / "physforge.db")
    monkeypatch.setattr(module, "UPLOAD_DIR", upload_dir)
    monkeypatch.setattr(module, "RESULTS_DIR", results_dir)
    module.processing_status.clear()
    module.init_db()

    yield module

    module.processing_status.clear()


@pytest.fixture()
def client(app_module):
    return TestClient(app_module.app)


def test_health_check_reports_ready_service(client):
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert payload["service"] == "PhysForge Simplified"
    assert payload["database"] == "ok"
    assert payload["job_count"] == 0
    assert payload["storage"]["uploads"] is True
    assert payload["storage"]["results"] is True


def test_upload_rejects_non_csv_files(client):
    response = client.post(
        "/api/upload",
        files={"file": ("sample.txt", b"x,t,u\n0,0,1\n", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Only CSV files are supported"


def test_upload_creates_job_and_runs_background_processor(client, app_module, monkeypatch):
    def fake_process_job(job_id, filepath):
        result = {
            "equation": "u_t = +0.010000*u_xx",
            "coefficients": {"u_xx": 0.01},
            "r_squared": 0.99,
            "mse": 0.001,
            "final_loss": 0.001,
            "epochs": 1,
            "terms_tested": ["u_xx"],
            "visualization": f"results/{job_id}.png",
            "quality": "excellent",
            "num_terms": 1,
        }
        with sqlite3.connect(app_module.DB_PATH) as conn:
            conn.execute(
                """
                UPDATE jobs
                SET status = 'completed',
                    completed_at = ?,
                    result_data = ?
                WHERE id = ?
                """,
                (datetime.now().isoformat(), json.dumps(result), job_id),
            )
        app_module.processing_status[job_id] = {
            "stage": "complete",
            "progress": "100%",
            "message": "Done",
        }

    monkeypatch.setattr(app_module, "process_job", fake_process_job)

    response = client.post(
        "/api/upload",
        files={"file": ("sample.csv", b"x,t,u\n0,0,1\n", "text/csv")},
    )

    assert response.status_code == 200
    job_id = response.json()["job_id"]
    assert (app_module.UPLOAD_DIR / f"{job_id}.csv").exists()

    job_response = client.get(f"/api/jobs/{job_id}")
    assert job_response.status_code == 200
    job = job_response.json()
    assert job["status"] == "completed"
    assert job["result"]["equation"] == "u_t = +0.010000*u_xx"
    assert job["processing"]["progress"] == "100%"


def test_visualization_endpoint_serves_existing_result_file(client, app_module):
    job_id = "test-job"
    (app_module.RESULTS_DIR / f"{job_id}.png").write_bytes(b"png-bytes")

    response = client.get(f"/api/results/{job_id}/visualization")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content == b"png-bytes"


def test_validate_dataset_requires_numeric_finite_columns(app_module):
    valid = pd.DataFrame({"x": [0.0], "t": [0.0], "u": [1.0], "extra": ["ok"]})
    validated = app_module.validate_dataset(valid)

    assert list(validated.columns) == ["x", "t", "u"]

    with pytest.raises(ValueError, match="CSV must contain columns"):
        app_module.validate_dataset(pd.DataFrame({"x": [0.0], "u": [1.0]}))

    with pytest.raises(ValueError, match="only numeric values"):
        app_module.validate_dataset(pd.DataFrame({"x": [0.0], "t": [0.0], "u": ["bad"]}))

    with pytest.raises(ValueError, match="only finite values"):
        app_module.validate_dataset(pd.DataFrame({"x": [0.0], "t": [0.0], "u": [np.inf]}))


def test_discover_equation_identifies_sparse_term(app_module, monkeypatch):
    def fake_compute_derivatives(_model, _x, _t):
        u = torch.zeros(4, 1)
        u_xx = torch.tensor([[1.0], [2.0], [3.0], [4.0]])
        zeros = torch.zeros(4, 1)
        return {
            "u": u,
            "u_x": zeros,
            "u_t": 0.5 * u_xx,
            "u_xx": u_xx,
            "u_tt": zeros,
            "u_xt": zeros,
            "u_xxx": zeros,
        }

    monkeypatch.setattr(app_module, "compute_derivatives", fake_compute_derivatives)

    (
        equation,
        coefficients,
        r_squared,
        terms_tested,
        stability_freq,
        coeff_std,
        derivative_stable,
    ) = app_module.discover_equation(
        model=None,
        x_data=np.arange(4),
        t_data=np.arange(4),
    )

    assert equation == "u_t = +0.500000*u_xx"
    assert coefficients == {"u_xx": pytest.approx(0.5)}
    assert r_squared == pytest.approx(1.0)
    assert "u_xxx" in terms_tested
    assert stability_freq["u_xx"] == pytest.approx(1.0)
    assert coeff_std["u_xx"] == pytest.approx(0.0)
    assert derivative_stable is None
