# PhysForge API Documentation

## Overview

This repository currently ships the simplified single-service PhysForge app in `app_simplified/`. It exposes a FastAPI API, stores job metadata in SQLite, saves uploaded CSV files locally, and writes generated visualizations to `app_simplified/results/`.

Run locally:
```bash
cd app_simplified
pip install -r requirements.txt
python app.py
```

Default local URL: `http://localhost:8000`

## Health

### GET `/health`
### GET `/api/health`

Returns service, database, and local storage readiness.

Example response:
```json
{
  "status": "healthy",
  "service": "PhysForge Simplified",
  "version": "1.0.0",
  "database": "ok",
  "job_count": 0,
  "storage": {
    "uploads": true,
    "results": true,
    "static": true
  }
}
```

## Web UI

### GET `/`

Serves the browser UI from `app_simplified/static/index.html`.

## Jobs

### POST `/api/upload`

Uploads a CSV file and queues background PINN training plus equation discovery.

Requirements:
- Multipart form field name: `file`
- Filename must end in `.csv`
- CSV must contain numeric finite columns: `x`, `t`, `u`

Example:
```bash
curl -X POST \
  -F "file=@app_simplified/sample_heat_equation.csv" \
  http://localhost:8000/api/upload
```

Response:
```json
{
  "job_id": "c3d8a7d4-7d65-4aa6-9c2d-70f07921f0f1",
  "status": "queued"
}
```

### GET `/api/jobs`

Lists jobs newest first.

Example response:
```json
[
  {
    "id": "c3d8a7d4-7d65-4aa6-9c2d-70f07921f0f1",
    "status": "completed",
    "dataset_name": "sample_heat_equation.csv",
    "created_at": "2026-05-19T10:30:00",
    "completed_at": "2026-05-19T10:33:00"
  }
]
```

### GET `/api/jobs/{job_id}`

Returns job status, saved result data, and current in-memory progress if the process is still running.

Completed job response includes:
```json
{
  "id": "c3d8a7d4-7d65-4aa6-9c2d-70f07921f0f1",
  "status": "completed",
  "dataset_name": "sample_heat_equation.csv",
  "created_at": "2026-05-19T10:30:00",
  "completed_at": "2026-05-19T10:33:00",
  "error": null,
  "result": {
    "equation": "u_t = +0.010000*u_xx",
    "coefficients": {
      "u_xx": 0.01
    },
    "r_squared": 0.99,
    "mse": 0.001,
    "final_loss": 0.001,
    "epochs": 1000,
    "terms_tested": ["u", "u_x", "u_xx", "u_tt", "u_xt", "u_xxx", "u²", "u³", "u*u_x", "u*u_xx", "u_x²"],
    "visualization": "results/c3d8a7d4-7d65-4aa6-9c2d-70f07921f0f1.png",
    "quality": "excellent",
    "num_terms": 1
  },
  "processing": null
}
```

### GET `/api/jobs/{job_id}/progress`

Returns in-memory progress for a running job.

Example:
```json
{
  "stage": "training",
  "progress": "400/1000",
  "message": "Epoch 400/1000 - Loss: 0.000123"
}
```

If the process has restarted or no progress is known:
```json
{
  "stage": "unknown",
  "progress": "N/A",
  "message": "No progress data available"
}
```

### GET `/api/results/{job_id}/visualization`

Returns the generated PNG visualization for a completed job.

## Error Responses

Common errors:
- `400` for unsupported upload types
- `404` for unknown jobs or missing visualizations
- `503` if the health check cannot reach SQLite
- `500` for unexpected processing failures, stored on the job as `status: failed`

## Notes

The older multi-service architecture described in early project notes is not part of the checked-in runnable code. The current implementation is intentionally a single deployable app for demos and portfolio use.
