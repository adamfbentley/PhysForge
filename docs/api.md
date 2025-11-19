# PhysForge API Documentation

## Overview
PhysForge is a Physics-Informed Scientific Discovery Platform that enables researchers to run PINN training, PDE discovery, derivative computation, and active experiment design jobs.

## Authentication
All API endpoints require JWT authentication except for `/auth/login` and `/auth/register`.

### Login
```bash
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=password
```

Response:
```json
{
  "access_token": "eyJ0eXAi...",
  "token_type": "bearer"
}
```

### Using the API
Include the JWT token in the Authorization header:
```
Authorization: Bearer eyJ0eXAi...
```

## Core Services

### 1. Authentication Service (Port 8000)
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get JWT token
- `GET /auth/me` - Get current user info
- `GET /auth/verify` - Verify JWT token (for API Gateway)

### 2. Data Management Service (Port 8001)
- `GET /datasets/` - List user's datasets
- `POST /datasets/` - Upload new dataset
- `GET /datasets/{id}` - Get dataset info
- `GET /datasets/{id}/download_link` - Get download link

### 3. Job Orchestration Service (Port 8002)
- `GET /jobs/` - List user's jobs
- `GET /jobs/{id}` - Get job status
- `POST /jobs/pinn-training` - Submit PINN training job
- `POST /jobs/derivatives` - Submit derivative computation job
- `POST /jobs/pde-discovery` - Submit PDE discovery job
- `POST /jobs/active-experiment` - Submit active experiment job
- `POST /jobs/{id}/cancel` - Cancel running job
- `GET /jobs/{id}/logs` - Get job logs

### 4. Reporting Service (Port 8003)
- `GET /reports/` - List user's reports
- `GET /reports/{id}` - Get report details
- `POST /reports/generate` - Generate new report

### 5. Audit Service (Port 8010)
- `POST /audit/events/` - Create audit event
- `GET /audit/events/` - Query audit events (admin only)
- `GET /audit/events/summary/` - Get audit summary (admin only)

## Job Types

### PINN Training
```json
{
  "job_type": "pinn_training",
  "config": {
    "model_config": {
      "layers": [2, 20, 20, 20, 20, 20, 20, 20, 20, 1],
      "activation": "tanh"
    },
    "training_config": {
      "learning_rate": 0.001,
      "epochs": 10000,
      "optimizer": "adam"
    },
    "data_config": {
      "dataset_id": 1,
      "collocation_points": 10000
    }
  }
}
```

### PDE Discovery
```json
{
  "job_type": "pde_discovery",
  "config": {
    "algorithm": "sindy",
    "data_path": "s3://datasets/experiment_data.h5",
    "feature_library": {
      "poly_order": 3,
      "include_sine": true,
      "include_cos": true
    },
    "sindy_config": {
      "threshold": 0.1,
      "max_iter": 20
    }
  }
}
```

### Derivative Computation
```json
{
  "job_type": "derivatives",
  "config": {
    "data_path": "s3://datasets/measurement_data.csv",
    "derivative_order": 2,
    "method": "finite_difference",
    "accuracy_order": 4
  }
}
```

### Active Experiment Design
```json
{
  "job_type": "active_experiment",
  "config": {
    "experiment_config": {
      "parameter_space": {
        "param1": {"min": 0, "max": 1},
        "param2": {"min": -1, "max": 1}
      },
      "objective_function": "some_function"
    },
    "data_path": "s3://datasets/prior_data.h5",
    "acquisition_function": "expected_improvement"
  }
}
```

## Error Handling

All endpoints return standard HTTP status codes:
- `200` - Success
- `400` - Bad Request (invalid input)
- `401` - Unauthorized (invalid/missing token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `429` - Too Many Requests (rate limited)
- `500` - Internal Server Error

Error response format:
```json
{
  "detail": "Error description"
}
```

## Rate Limiting

- Authentication endpoints: 10 requests/minute
- General API endpoints: 100 requests/minute
- File uploads: 5 uploads/5 minutes

## File Uploads

Datasets are uploaded as multipart/form-data:
```bash
curl -X POST \
  -H "Authorization: Bearer <token>" \
  -F "file=@data.csv" \
  -F "name=My Dataset" \
  -F "description=Experimental data" \
  http://localhost:8001/datasets/
```

Supported formats: CSV, HDF5, JSON, TXT, NPY, NPZ

## Job Monitoring

Jobs progress through states: PENDING → RUNNING → COMPLETED/FAILED

Monitor progress:
```bash
# Get job status
curl -H "Authorization: Bearer <token>" \
  http://localhost:8002/jobs/123

# Get job logs
curl -H "Authorization: Bearer <token>" \
  http://localhost:8002/jobs/123/logs
```

## Data Storage

- **Metadata**: PostgreSQL databases
- **Files**: MinIO object storage
- **Cache/Queue**: Redis
- **Audit Logs**: Separate PostgreSQL database

## Security

- JWT-based authentication
- Role-based access control (RBAC)
- Input validation and sanitization
- Rate limiting
- Security headers
- Audit logging
- File type validation