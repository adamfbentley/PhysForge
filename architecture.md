# Architecture Documentation for Physics-Informed Scientific Discovery Platform

## Overview

The Physics-Informed Scientific Discovery Platform is a comprehensive system designed to accelerate scientific research by integrating machine learning techniques with fundamental physics principles. The platform enables users to train Physics-Informed Neural Networks (PINNs), discover Partial Differential Equations (PDEs) through symbolic regression, and perform active experiment design.

The system is architected as a microservices-based application with a React frontend and multiple FastAPI backend services, orchestrated via Redis Queue (RQ) for job management. Data is stored in PostgreSQL databases and MinIO object storage.

## High-Level Architecture

```
┌─────────────────┐    ┌──────────────────┐
│   React Frontend│────│  API Gateway     │  (Not Implemented)
│                 │    │  (Nginx/Traefik) │
└─────────────────┘    └──────────────────┘
         │                       │
         └───────────────────────┼─────────────────────────────┐
                                 │                             │
                    ┌────────────▼────────────┐    ┌───────────▼──────────┐
                    │  Auth Service          │    │  Data Management     │
                    │  (JWT, RBAC)           │    │  Service              │
                    └───────────────────────┘    └───────────────────────┘
                                 │                             │
                    ┌────────────▼────────────┐    ┌───────────▼──────────┐
                    │  Job Orchestration     │    │  CLI Service         │
                    │  Service (RQ)          │    │  (Typer CLI)         │
                    └───────────────────────┘    └───────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │    Compute Workers     │
                    │  (Docker/Firecracker)  │
                    ├────────────────────────┤
                    │  PINN Training Worker  │
                    │  Derivative Worker     │
                    │  PDE Discovery Worker  │
                    │  Active Experiment W.  │
                    └────────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  Reporting Service     │
                    └────────────────────────┘

Infrastructure:
- PostgreSQL (per service databases)
- Redis (job queue)
- MinIO/S3 (object storage)
- Prometheus/Grafana (monitoring - Not Implemented)
- Audit Log Service (Not Implemented)
```

## Services Detail

### Auth Service (COMP-BE-02)

**Purpose:** Manages user authentication using JWT tokens and role-based access control (RBAC).

**Components:**
- `main.py`: FastAPI app with lifespan management
- `models.py`: User and Role SQLAlchemy models with many-to-many relationship
- `schemas.py`: Pydantic schemas for users, roles, tokens
- `crud.py`: Database operations for users and roles
- `security.py`: JWT token creation/validation, password hashing
- `routers/auth.py`: Endpoints for register, login, user management, role assignment
- `database.py`: SQLAlchemy engine and session management
- `config.py`: Settings for DB, JWT, environment
- Tests: Comprehensive test suite with pytest

**Status:** Fully implemented with tests. Supports user registration, login, role management.

**Production Readiness:** High. Includes security best practices (no hardcoded secrets, bcrypt hashing).

**TODO:** None major.

### Data Management Service (COMP-BE-03)

**Purpose:** Handles ingestion, storage, and management of scientific datasets with metadata extraction and versioning.

**Components:**
- `main.py`: FastAPI app
- `models.py`: Dataset and DatasetVersion models
- `schemas.py`: Pydantic schemas
- `crud.py`: DB operations
- `routers/datasets.py`: Upload, list, download datasets
- `object_storage.py`: MinIO integration for file storage
- `metadata_extractor.py`: Extracts metadata from HDF5, JSON, generic files
- `security.py`: JWT validation (no creation)
- `database.py`, `config.py`

**Status:** Fully implemented. Supports HDF5, NetCDF, CSV, NumPy, VTK, JSON formats. Automatic versioning, presigned download URLs.

**Production Readiness:** High. Includes metadata extraction, secure storage.

**TODO:** Support for more formats if needed.

### Job Orchestration Service (COMP-BE-04)

**Purpose:** Manages lifecycle of long-running computational jobs using Redis Queue.

**Components:**
- `main.py`: FastAPI app
- `models.py`: Job and JobStatusLog models
- `schemas.py`: Job schemas (missing specific job creation schemas like PinnTrainingJobCreate)
- `crud.py`: DB operations (create_job function doesn't match router calls)
- `routers/jobs.py`: Endpoints to submit PINN, derivative, PDE discovery, active experiment jobs
- `worker.py`: RQ worker runner
- `storage_utils.py`: MinIO client for fetching results
- `database.py`, `config.py`

**Status:** Partially implemented. Routers call non-existent schemas and mismatched crud functions. Basic job tracking works, but specific job configs are missing.

**Production Readiness:** Low. Missing job creation schemas, crud mismatches.

**TODO:**
- Define PinnTrainingJobCreate, DerivativeComputationJobCreate, PDEDiscoveryJobCreate, ActiveExperimentJobCreate schemas
- Fix crud.create_job to accept job_type and config
- Implement job listing, status retrieval endpoints

### PINN Training Service (Worker)

**Purpose:** Executes PINN training jobs in isolated workers.

**Components:**
- `worker_task.py`: Main RQ task for PINN training
- `pinn_config.py`: Comprehensive config for networks, training, physics loss
- `pinn_model.py`: MLP, FourierFeatureMLP, DeepONet implementations
- `pinn_solver.py`: Training logic with Adam/LBFGS, loss weighting
- `pinn_results.py`: Result schemas
- `storage_utils.py`: Save models/logs to MinIO
- `config.py`

**Status:** Fully implemented. Supports multiple architectures, loss functions, optimizers.

**Production Readiness:** High. Includes checkpointing, logging, error handling.

**TODO:** None major.

### Derivative & Feature Service (Worker)

**Purpose:** Computes derivatives from PINN outputs and generates feature libraries.

**Components:**
- `worker_task.py`: RQ task for derivative computation and feature generation
- `derivative_calculator.py`: AD-based derivative computation
- `feature_generator.py`: Generates polynomial, nonlinear features
- `schemas.py`: Config schemas
- `storage_utils.py`: Save to MinIO
- `config.py`

**Status:** Implemented. Computes up to 3rd order derivatives, generates rich feature libraries.

**Production Readiness:** High.

**TODO:** None.

### PDE Discovery Service (Worker)

**Purpose:** Discovers PDEs using SINDy and PySR symbolic regression.

**Components:**
- `worker_task.py`: RQ task for PDE discovery
- `sindy_discovery.py`: Sparse regression with SINDy
- `pysr_discovery.py`: Symbolic regression with PySR
- `symbolic_utils.py`: Equation canonicalization
- `model_ranking.py`: Ranks models by metrics
- `sensitivity_analysis.py`: Uncertainty analysis
- `metrics_utils.py`: AIC/BIC calculation
- `schemas.py`, `crud.py`, `models.py`, `database.py`
- `storage_utils.py`

**Status:** Fully implemented. Supports SINDy, PySR, model selection, uncertainty quantification.

**Production Readiness:** High.

**TODO:** None.

### Active Experiment Service (Worker)

**Purpose:** Proposes optimal experiments/simulations for information gain.

**Components:**
- `main.py`: FastAPI app (but no routers implemented?)
- `worker_task.py`: RQ task for active experiment design
- `experiment_designer.py`: LHS sampling, Bayesian optimization
- `schemas.py`, `crud.py`, `models.py`, `database.py`
- `storage_utils.py`

**Status:** Worker implemented. Supports parameter sweep suggestions, Bayesian optimization.

**Production Readiness:** High for worker.

**TODO:** Implement API endpoints in main.py/routers if needed.

### Reporting Service (COMP-BE-10)

**Purpose:** Generates discovery reports and Jupyter Notebooks.

**Components:**
- `main.py`: FastAPI app
- `routers/reports.py`: Submit report jobs, retrieve reports
- `worker_task.py`: Generates reports/notebooks
- `models.py`, `schemas.py`, `crud.py`
- `storage_utils.py`

**Status:** Implemented. Creates reproducible notebooks.

**Production Readiness:** High.

**TODO:** None.

### CLI Service (COMP-BE-11)

**Purpose:** Command-line interface for programmatic interaction.

**Components:**
- `main.py`: Typer app
- `auth_cli.py`, `dataset_cli.py`, `job_cli.py`: CLI commands

**Status:** Basic structure. Commands for auth, datasets, jobs.

**Production Readiness:** Medium. Needs full implementation of commands.

**TODO:** Implement CLI logic for all operations.

## Frontend

**Technology:** React 18 + TypeScript + Tailwind CSS + Axios

**Components:**
- `App.tsx`: Router setup
- `pages/`: Home, PdeComparisonPage
- `components/`: EquationEditor (assumed)
- `api/`: API client functions

**Status:** Basic. Home page and PDE comparison page, but data fetching disabled due to auth issues.

**Production Readiness:** Low. Minimal UI, no auth integration, hardcoded mocks.

**TODO:**
- Implement authentication UI
- Build full dashboard for dataset management, job submission, results visualization
- Integrate with backend APIs
- Add 3D visualization (Three.js mentioned in README)
- Implement interactive equation editor

## Infrastructure & Shared Components

### Databases
- **PostgreSQL:** Separate databases for each service (auth_db, data_db, job_db, etc.)
- **Status:** Schemas defined, but no migrations/Alembic setup.

### Message Queue
- **Redis + RQ:** Job queuing and worker management
- **Status:** Configured, workers implemented.

### Object Storage
- **MinIO/S3:** Stores datasets, models, logs, reports
- **Status:** Integrated in services.

### Monitoring & Observability (Not Implemented)
- **Prometheus/Grafana:** For metrics and dashboards
- **Status:** Mentioned in README, not implemented.

### API Gateway (Not Implemented)
- **Nginx/Traefik:** Unified entry point, load balancing, security
- **Status:** Not implemented. Services run independently.

### Audit Logging (Not Implemented)
- **Status:** Not implemented.

### Compute Workers
- **Docker/Firecracker:** Sandboxed execution
- **Status:** Workers are Python scripts, not containerized.

## Current Status Summary

**Implemented Services:**
- Auth Service: Complete with tests
- Data Management Service: Complete
- PINN Training Worker: Complete
- Derivative Worker: Complete
- PDE Discovery Worker: Complete
- Active Experiment Worker: Complete
- Reporting Service: Complete

**Partially Implemented:**
- Job Orchestration Service: Missing schemas and crud fixes
- CLI Service: Basic structure
- Frontend: Minimal UI

**Not Implemented:**
- API Gateway
- Monitoring Service
- Audit Log Service
- Containerization of workers
- Kubernetes deployment
- Jupyter Notebook generation (mentioned but not in code)

**Mock/Simplified Implementations:**
- Frontend: No real data integration
- Job Orchestration: Incomplete job submission schemas
- CLI: Placeholder commands

## Production Readiness Checklist

### Security
- [x] JWT authentication
- [x] Password hashing (bcrypt)
- [x] RBAC
- [ ] API Gateway with rate limiting
- [ ] Audit logging
- [ ] Input validation/sanitization
- [ ] HTTPS configuration

### Scalability
- [x] Microservices architecture
- [ ] Containerization (workers not containerized)
- [ ] Kubernetes manifests
- [ ] Load balancing
- [ ] Horizontal scaling configs

### Reliability
- [x] Job queuing with Redis
- [ ] Monitoring/Metrics
- [ ] Health checks
- [ ] Error handling and retries
- [ ] Backup strategies

### Data Management
- [x] Versioned datasets
- [x] Object storage
- [ ] Data retention policies
- [ ] Backup/DR for MinIO

### Development/Operations
- [ ] CI/CD pipelines
- [ ] Database migrations (Alembic)
- [ ] Environment configs
- [ ] Logging aggregation
- [ ] Documentation

### Performance
- [x] GPU support in workers
- [ ] Caching layers
- [ ] Async processing optimizations

## Major TODOs for Production

1. **Fix Job Orchestration Service:**
   - Define missing job creation schemas
   - Update crud.create_job to handle job_type and config
   - Add job listing and status endpoints

2. **Implement API Gateway:**
   - Set up Nginx/Traefik for routing and load balancing
   - Add authentication middleware

3. **Containerize and Orchestrate:**
   - Dockerize all services and workers
   - Create docker-compose for local dev
   - Kubernetes manifests for production

4. **Complete Frontend:**
   - Implement authentication flow
   - Build comprehensive UI for all features
   - Integrate 3D visualizations
   - Add real-time job monitoring

5. **Add Monitoring:**
   - Prometheus metrics
   - Grafana dashboards
   - Alerting rules

6. **Implement Audit Logging:**
   - Centralized audit service
   - Log all user actions and data access

7. **Database Migrations:**
   - Set up Alembic for schema migrations
   - Handle production DB updates

8. **Complete CLI Service:**
   - Implement all CLI commands for full programmatic access

9. **Security Hardening:**
   - Penetration testing
   - Security headers
   - CORS configuration
   - Secret management (Vault?)

10. **Documentation and Testing:**
    - API documentation (Swagger)
    - End-to-end tests
    - User guides
    - Performance benchmarks

## Conclusion

The platform has a solid foundation with most core scientific computation services implemented and tested. The main gaps are in orchestration, frontend completeness, and production infrastructure. The architecture is well-designed for scalability, but requires completion of the integration layers and operational tooling to reach production readiness.</content>
<parameter name="filePath">C:\Users\ebentley2\Downloads\PhysForge_-_Meta-Simulation\architecture.md