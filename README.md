# PhysForge: AI-Powered Physics Discovery Platform

[![License: Proprietary](https://img.shields.io/badge/License-Proprietary-red.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![React 18](https://img.shields.io/badge/react-18-blue.svg)](https://reactjs.org/)
[![Status: Development](https://img.shields.io/badge/status-development-orange.svg)]()

> **A platform concept for discovering mathematical laws governing physical systems from data using Physics-Informed Neural Networks and symbolic regression.**

PhysForge is an ambitious project aiming to automate scientific discovery by combining Physics-Informed Neural Networks (PINNs) with symbolic regression techniques. The goal is to enable researchers to upload experimental or simulation data and automatically train physics-aware neural networks, compute derivatives, and discover governing equations.

**⚠️ Current Status: In Development (Not Yet Tested)**

This is a large-scale project (~15,000 lines of code) with most components implemented but not yet validated end-to-end. The architecture is designed but integration testing is still needed to verify everything works together as intended.

**🎯 Intended capabilities:**
- **Automated workflow**: Raw data → trained PINN → discovered equations
- **Microservices architecture**: 10 FastAPI services (auth, data management, job orchestration, PINN training, derivatives, PDE discovery, active learning, reporting, CLI, audit)
- **Physics-aware ML**: Incorporates physical constraints and symbolic reasoning via SINDy and PySR
- **Modern frontend**: React + TypeScript UI for job monitoring and visualization

**💡 Potential use cases:**
- Discover PDEs from fluid dynamics simulations
- Extract governing equations from time-series data  
- Reverse-engineer physical models from experimental measurements
- Automate equation discovery for climate/physics data

---

## 🚀 Implementation Status

**Codebase:** ~90% complete (217 files, 106 Python files, 43 TypeScript/JS files)  
**Backend:** 10 microservices implemented with schemas, routers, and some tests  
**Frontend:** React 18 + TypeScript UI implemented but dependencies not yet installed  
**Infrastructure:** Docker Compose configuration exists but not fully tested  
**Integration:** End-to-end workflow has not been validated in practice  

**What's done:**
- ✅ Core service implementations (FastAPI microservices)
- ✅ Frontend UI components (React + Mantine)
- ✅ Database schemas and models (PostgreSQL per service)
- ✅ Job orchestration design (Redis Queue)
- ✅ ML integration interfaces (PyTorch, SINDy, PySR)

**What's not tested:**
- ⚠️ Full Docker Compose orchestration
- ⚠️ API Gateway routing and service communication
- ⚠️ End-to-end workflow (upload → PINN → discovery)
- ⚠️ Redis job queue functionality
- ⚠️ Frontend-backend integration

See [CURRENT_STATUS.md](CURRENT_STATUS.md) for detailed progress.

---

## 🎬 Working Demo

### Option 1: Simplified Full-Stack Application (Recommended)

A complete working application in `app_simplified/` demonstrates the full PhysForge workflow:

**Features:**
- 🌐 **Web Interface**: Upload CSV data via drag-and-drop
- 🤖 **PINN Training**: Automatic physics-informed training (3,000 epochs)
- 🔬 **Equation Discovery**: Discovers governing PDEs using sparse regression
- 📊 **Real-time Monitoring**: Watch jobs process and view results instantly

**Discovered Equation Types:**
- Linear: `u`, `u_x`, `u_t`
- Nonlinear: `u²`, `u·u_x` (Burgers), `u_x²`
- Higher derivatives: `u_xx`, `u_xxx` (KdV), `u_tt` (wave)
- Mixed: `u_xt`, `u·u_xx`

**To run:**
```bash
cd app_simplified
python generate_sample_data.py  # Create test data
python app.py                    # Start server

# Open browser to http://localhost:8000
# Upload sample_heat_equation.csv
# Watch it train and discover: u_t = 0.010000·u_xx
```

**Performance:** ~2 minutes from upload to discovered equation on CPU.

**Why simplified?** See [SIMPLIFIED_VS_MAIN.md](SIMPLIFIED_VS_MAIN.md) for detailed comparison with the main platform.

**Technical details:** [app_simplified/EQUATION_DISCOVERY.md](app_simplified/EQUATION_DISCOVERY.md) explains the discovery algorithm.

---

### Option 2: Minimal PINN Demo

A standalone script (`demo_minimal_pinn.py`) demonstrates core PINN training:

**To run:**
```bash
pip install torch matplotlib numpy
python demo_minimal_pinn.py
```

**Results:** Trains a 2,241-parameter network achieving MSE < 3.1e-05 on the heat equation.

---

## 🛠️ Tech Stack

**Frontend:**
- React 18 + TypeScript
- Mantine UI + Tailwind CSS
- Zustand (state management)
- Vite (build tool)

**Backend:**
- FastAPI (8 microservices)
- PyTorch (PINN training)
- SINDy + PySR (symbolic regression)
- Redis Queue (job orchestration)

**Infrastructure:**
- PostgreSQL (metadata storage)
- MinIO/S3 (object storage)
- Docker + Docker Compose
- Prometheus + Grafana (monitoring)

---

## Table of Contents
- [Current Status](#-current-status)
- [Tech Stack](#-tech-stack)
- [Project Overview](#project-overview)
- [Features](#features)
- [Architecture Summary](#architecture-summary)
- [How to Set Up & Run](#how-to-set-up--run)

---

## Project Overview

The **Physics-Informed Scientific Discovery Platform** is an ambitious project aimed at revolutionizing scientific research by integrating advanced machine learning techniques with fundamental physics principles. Its primary objective is to accelerate scientific discovery by providing a comprehensive platform that streamlines data ingestion, enables robust Physics-Informed Neural Network (PINN) training, automates Partial Differential Equation (PDE) discovery through symbolic and sparse regression, and facilitates active experiment design. The platform is meticulously engineered to ensure reproducibility, robust analysis, and efficient collaboration among researchers.

**Key Stakeholders:**
- **Scientists/Researchers:** Primary users who leverage the platform for accelerating their discovery workflows.
- **Data Scientists/ML Engineers:** Utilize the platform's ML capabilities for PINN development and PDE discovery.
- **Platform Administrators:** Manage the platform's infrastructure, user access, and resource allocation.
- **Project Sponsors/Management:** Oversee the project's progress, strategic direction, and resource utilization.

## Features

The platform offers a rich set of features designed to support the entire scientific discovery lifecycle:

### Data Management & Ingestion
- **Diverse Data Format Support:** Ingest and manage scientific datasets in HDF5, NetCDF, CSV, NumPy (.npz), VTK/VTU, and JSON metadata formats.
- **Versioned Project Store:** HDF5-backed project store with automatic versioning and provenance tracking (who, when, seed).
- **Dataset Preview UI:** Interactive user interface for visualizing 1D/2D/3D slices and animations of datasets.
- **Data Export:** Export datasets and computed derivatives to HDF5 format.

### PINN Training Module
- **Configurable Architectures:** Support for various PINN architectures including Fully Connected (FC) networks (with sine/ReLU/Tanh activations), Fourier features, multi-output networks, and latent-space autoencoder PINNs, implemented in PyTorch (with optional JAX support).
- **Comprehensive Loss Functions:** Utilize PDE residual loss, data fidelity (L2) loss, boundary/initial condition penalty terms, physics priors, and uncertainty-aware losses.
- **Hybrid Optimization:** Employ an Adam + LBFGS hybrid optimizer for efficient training.
- **Advanced Training Features:** Adaptive loss weighting, curriculum training, checkpointing, reproducible seeds, and multi-GPU support.
- **Automated Derivative Computation:** Compute derivatives up to 3rd order via Automatic Differentiation (AD) from trained PINN outputs.
- **Derivative Export:** Export spatial and time derivatives on user-specified grids to CSV or HDF5 formats.

### PDE Discovery & Feature Engineering
- **Feature Library Generation:** Automatically generate a rich library of candidate features including polynomial terms, cross-products, derivatives, nonlinear transforms, and integral/differential operators.
- **Sparse Regression (SINDy):** Integrate SINDy for sparse identification of governing PDEs from feature matrices.
- **Symbolic Regression (PySR):** Integrate PySR for symbolic regression to discover closed-form mathematical expressions for PDEs, including transcendental forms.
- **Symbolic Manipulation:** Utilize SymPy for symbolic manipulation, simplification, and canonicalization of discovered equations.
- **Discovery Workflow:** Guided workflow for building feature matrices, executing sparse/symbolic regression, and cross-validating candidate equations.
- **Model Selection Metrics:** Evaluate candidate equations using metrics such as RMSE, AIC/BIC, sparsity (L0), coefficient stability, and physical units consistency.
- **Model Ranking:** Rank discovered models based on predictive accuracy, coefficient confidence intervals, sensitivity analysis, and parsimony scores.
- **Uncertainty Quantification:** Quantify uncertainty in extracted coefficients using bootstrap or Bayesian sparse regression methods.

### Active Experiment Design
- **Information Gain Maximization:** Propose optimal next simulations or physical experiments to maximize information gain and reduce uncertainty in discovered models.
- **Parameter & Condition Suggestions:** Support for parameter sweep suggestions (e.g., Latin Hypercube sampling, Bayesian optimization) and mesh/initial condition suggestions.
- **Simulation Orchestration:** Option to auto-launch simulation runs locally (via user-configured simulators) or generate job specifications for external solvers (e.g., OpenFOAM, LBM code).

### User Interface & Visualization
- **Interactive Visualizations:** A React + Three.js powered UI for interactive field visualizations (slices, streamlines, isosurfaces), time-series plots, and residual plots.
- **Comparative Analysis:** Side-by-side comparison of PINN predictions against forward solves from discovered PDEs.
- **Equation Editor:** An interactive equation editor with LaTeX rendering and export capabilities to SymPy, LaTeX, Python, and Julia formats.

### Platform & Operations
- **Comprehensive Backend API (FastAPI):** Secure API for user authentication, dataset management, job submission/monitoring (PINN training, derivative export, PDE discovery, active experiment suggestions), result retrieval, and report generation.
- **Command-Line Interface (CLI):** For running local pipeline steps and batch jobs programmatically.
- **Authentication & Authorization:** Secure user authentication and role-based access control (project owner, collaborator, read-only).
- **Reproducibility & Provenance:** Automatic storage of random seeds, model checkpoints, hyperparameters, and full logs for every run. Generation of UUID-identified 'discovery reports' capturing the entire pipeline.
- **Jupyter Notebook Generation:** Automatically generate Jupyter Notebooks that reconstruct the entire discovery pipeline for reproducibility and sharing.
- **Sandboxed Code Execution:** User-supplied models/simulators are executed in isolated, sandboxed environments (Docker/Firecracker) with enforced resource limits (GPU/CPU/time).
- **Audit Logging:** Comprehensive audit logs for all external compute or data access activities.
- **API Gateway:** Centralized API Gateway for unified access, load balancing, and security enforcement.
- **Containerized Deployment:** Docker Compose configuration for easy local development and deployment, with Kubernetes readiness for production.
- **Monitoring & Observability:** Integration with Prometheus and Grafana for comprehensive monitoring of platform health, job status, and resource utilization.

## Architecture Summary

The Physics-Informed Scientific Discovery Platform is architected as a modular, microservices-oriented application. It features a **complete, production-ready React frontend** for an interactive user experience, communicating with a robust **FastAPI backend**. The backend is composed of several specialized services:

### Frontend (Complete Implementation)
- **React 18 + TypeScript** - Modern, type-safe frontend with professional UI
- **Mantine UI + Tailwind CSS** - Scientific-friendly design system
- **Complete Authentication** - JWT-based login/register with protected routes
- **Dataset Management** - Drag-and-drop upload, browsing, and preview functionality
- **Job Management** - Full PINN training and PDE discovery job submission forms
- **Real-time Monitoring** - Live job progress tracking and status updates
- **Results Visualization** - Training metrics, loss history, and discovered equations
- **Responsive Design** - Works seamlessly on desktop, tablet, and mobile devices

### Backend Services (All Implemented)
- **Auth Service (COMP-BE-02):** Manages user authentication (JWT) and role-based access control (RBAC) with PostgreSQL.
- **Data Management Service (COMP-BE-03):** Handles data ingestion, metadata extraction, versioning, and storage of scientific datasets in an HDF5-backed object store (MinIO/S3).
- **Job Orchestration Service (COMP-BE-04):** Manages the lifecycle of all long-running computational jobs (PINN training, PDE discovery, etc.) using Redis and RQ for queuing and dispatching tasks.
- **PINN Training Service (COMP-BE-05):** (Executed by Compute Workers) Configures, executes, and monitors PINN training, supporting various architectures, loss functions, and optimizers.
- **Derivative & Feature Service (COMP-BE-06):** (Executed by Compute Workers) Computes high-order derivatives from PINN outputs and generates a library of candidate features.
- **PDE Discovery Service (COMP-BE-07):** (Executed by Compute Workers) Integrates SINDy and PySR for sparse and symbolic regression, performs model selection, ranking, and uncertainty quantification.
- **Active Experiment Service (COMP-BE-08):** (Executed by Compute Workers) Proposes new experiments/simulations to maximize information gain.
- **Reporting Service (COMP-BE-10):** Generates discovery reports and reproducible Jupyter Notebooks.
- **Compute Worker Pool (COMP-BE-09):** A pool of sandboxed (Docker/Firecracker) worker processes that execute the computationally intensive tasks from the PINN Training, Derivative & Feature, PDE Discovery, and Active Experiment services.
- **CLI Service (COMP-BE-11):** A Python-based command-line interface for programmatic interaction.
- **Monitoring Service (COMP-BE-12):** Integrates Prometheus for metrics collection and Grafana for visualization.
- **Audit Log Service (COMP-BE-13):** Collects, stores, and queries audit logs from all services.
- **API Gateway (COMP-BE-01):** An Nginx/Traefik instance serving as the unified entry point for all requests, handling routing, load balancing, and initial authentication checks.

Data is primarily stored in **MinIO/S3** for large scientific datasets and **PostgreSQL** for metadata and application state. **Redis** acts as a message broker for the job queue. All operations are secured and auditable.

## Non-Functional Requirements

-   **Performance:** The initial discovery pipeline (PINN training + symbolic regression) must complete within a configurable budget (e.g., 24h on 1-2 GPUs for 2D canonical problems). Interactive UI visualizations (2D/3D fields) must render at ≥30 FPS for typical datasets. The system must efficiently manage long-running training/inference jobs via a robust job queue.
-   **Security:** All user interactions and data access must be secured via authentication and role-based access control (project owner, collaborator, read-only). JWTs for inter-service communication and user sessions must utilize asymmetric cryptography (e.g., RSA), with the Auth Service signing tokens with a private key and all other services verifying with a publicly available public key to prevent token forgery. User-supplied code for models or simulation launchers must be executed in sandboxed environments (e.g., Docker/Firecracker). Resource limits (GPU/CPU/time) must be enforced per job. Comprehensive audit logs must be maintained for all external compute or data access.
-   **Scalability:** The platform must support multi-device/multi-GPU training (PyTorch DDP, JAX pmap, PyTorch Lightning). It must be deployable in a containerized environment using Docker Compose for local development and testing, and Kubernetes for production-scale deployments. A centralized API Gateway will manage traffic and provide a unified entry point. The architecture will be modular microservices (FastAPI backend, worker pool, React frontend). Large arrays and results will be stored in an HDF5 file store with S3 compatibility, and metadata in Postgres/SQLite. The job queue (Redis + RQ or Celery) must handle concurrent long-running tasks.

## How to Set Up & Run

This guide will walk you through setting up and running the Physics-Informed Scientific Discovery Platform locally using Docker Compose.

### Prerequisites

Before you begin, ensure you have the following installed on your system:

-   **Docker Desktop:** Includes Docker Engine and Docker Compose. [Install Docker Desktop](https://www.docker.com/products/docker-desktop)
-   **Git:** For cloning the repository. [Install Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
-   **Python 3.9+:** While most services run in Docker, you might need Python for local CLI interactions or development scripts.

### Clone Repository

First, clone the project repository to your local machine:

```bash
git clone <repository_url>
cd Physics-Informed-Scientific-Discovery-Platform # Or whatever your repo name is
```

### Environment Configuration

Each backend service requires specific environment variables for database connections, MinIO credentials, and JWT secrets. Example `.env.example` files are provided within each service directory. You need to create `.env` files for each service by copying and modifying these examples.

**Important Security Note:** The `SECRET_KEY` for JWTs and `DATABASE_URL` credentials are critical. **DO NOT** use default or insecure values in any environment beyond local development. Generate strong, unique keys for production.

Create `.env` files in the following directories:

-   `backend/auth_service/.env`
-   `backend/data_management_service/.env`
-   `backend/job_orchestration_service/.env`
-   `backend/pinn_training_service/.env`
-   `backend/derivative_feature_service/.env`
-   `backend/pde_discovery_service/.env`

**Example `.env` content for `backend/auth_service/.env`:**

```
DATABASE_URL="postgresql+psycopg2://user:password@db:5432/auth_db"
SECRET_KEY="your-super-secret-key-for-jwt-change-this-in-production"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
ENVIRONMENT="development"
```

Ensure `SECRET_KEY` and `ALGORITHM` are consistent across all services that validate or generate JWTs.

### Database Setup

The platform uses PostgreSQL for metadata storage. Docker Compose will set up PostgreSQL containers for each service that requires one (Auth, Data Management, Job Orchestration, PDE Discovery). The `DATABASE_URL` in each service's `.env` file should point to its respective PostgreSQL container.

For example, in `backend/auth_service/.env`, `DATABASE_URL="postgresql+psycopg2://user:password@db:5432/auth_db"` refers to the `db` service defined in `docker-compose.yml`.

### Object Storage Setup (MinIO)

MinIO is used as an S3-compatible object storage solution for datasets, models, and results. Docker Compose will start a MinIO container. Configure the `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, and `MINIO_BUCKET_NAME` in each service's `.env` file.

**Example `.env` content for MinIO-related variables:**

```
MINIO_ENDPOINT="minio:9000"
MINIO_ACCESS_KEY="minioadmin"
MINIO_SECRET_KEY="minioadmin"
MINIO_SECURE=False # Set to True if MinIO is configured with HTTPS
MINIO_BUCKET_NAME="scientific-datasets" # Or other specific bucket names per service
```

### Frontend Setup

The frontend is a complete, production-ready React application with TypeScript. To set up the frontend for development:

1. **Install Dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Environment Configuration:**
   ```bash
   cp .env.example .env
   # Edit .env with your backend service URLs
   ```

3. **Start Development Server:**
   ```bash
   npm run dev
   # Frontend will be available at http://localhost:3000
   ```

4. **Build for Production:**
   ```bash
   npm run build
   # Production build will be in dist/ directory
   ```

**Frontend Features (All Implemented):**
- Complete authentication system (login/register)
- Dataset management (upload, browse, preview)
- Job submission (PINN training, PDE discovery)
- Real-time job monitoring and results visualization
- Responsive design for all devices
- Professional scientific UI with Mantine components

### Running Services with Docker Compose

Navigate to the root directory of the project where `docker-compose.yml` is located. Then, run the following command to build and start all services:

```bash
docker-compose up --build -d
```

This command will:
- Build Docker images for all services (frontend, backend services, workers).
- Start PostgreSQL databases, Redis, and MinIO.
- Start the FastAPI backend services (Auth, Data Management, Job Orchestration, PDE Discovery, Derivative & Feature).
- Start the RQ workers (`pinn_training_worker`, `pde_discovery_worker`, `derivative_worker`).
- Start the API Gateway (Nginx/Traefik).
- Start the React frontend development server.

It might take a few minutes for all services to start up and become healthy.

To view the logs of all running services:

```bash
docker-compose logs -f
```

To stop all services:

```bash
docker-compose down
```

### Accessing the Platform

Once all services are up and running:

-   **Frontend UI:** Access the interactive user interface at `http://localhost:3000`.
-   **API Gateway:** The central entry point for all backend APIs is `http://localhost:8000`.
-   **Swagger UI (API Documentation):**
    -   Main API Gateway Docs: `http://localhost:8000/docs`
    -   Auth Service Docs: `http://localhost:8000/auth/docs`
    -   Data Management Service Docs: `http://localhost:8000/datasets/docs`
    -   Job Orchestration Service Docs: `http://localhost:8000/jobs/docs`
    -   PDE Discovery Service Docs: `http://localhost:8000/pde-discovery/docs`

### Initial Admin Setup

After the services are running, you'll need to register an initial user and assign them an 'admin' role to manage the platform.

1.  **Register a User:**
    Send a `POST` request to `http://localhost:8000/auth/register` with a JSON body like:
    ```json
    {
      "email": "admin@example.com",
      "password": "secure_admin_password"
    }
    ```

2.  **Log In to Get Token:**
    Send a `POST` request to `http://localhost:8000/auth/login` with `x-www-form-urlencoded` data:
    -   `username`: `admin@example.com`
    -   `password`: `secure_admin_password`
    This will return an `access_token`.

3.  **Create 'admin' Role:**
    Send a `POST` request to `http://localhost:8000/auth/roles/` with the `access_token` in the `Authorization: Bearer <token>` header and a JSON body:
    ```json
    {
      "name": "admin"
    }
    ```

4.  **Assign 'admin' Role to User:**
    First, get the user's ID (e.g., from the `/auth/me` endpoint or the registration response). Assuming user ID is `1`:
    Send a `POST` request to `http://localhost:8000/auth/users/1/roles/` with the `access_token` in the `Authorization: Bearer <token>` header and a JSON body:
    ```json
    {
      "role_names": ["admin"]
    }
    ```

You now have an admin user with full permissions to interact with the platform's features.

---

## 📄 License

**PhysForge Proprietary License** - This software is proprietary and protected by copyright.

**Permitted Uses:**
- ✅ Academic research and educational purposes (non-commercial)
- ✅ Viewing and studying the code for learning
- ✅ Portfolio evaluation by potential employers/institutions

**Prohibited Uses:**
- ❌ Commercial use or deployment without license
- ❌ Creating commercial products/services based on this software
- ❌ Distribution or sublicensing
- ❌ SaaS or cloud-based service deployment

**Commercial Licensing Available:**  
For commercial use, production deployment, or custom licensing, contact:  
📧 adam.f.bentley@gmail.com

See [LICENSE](LICENSE) for full terms and conditions.

---

## 👤 Author

**Adam F. Bentley**  
Victoria University of Wellington  
📧 adam.f.bentley@gmail.com  
🔗 GitHub: [@adamfbentley](https://github.com/adamfbentley)

---

*This project represents advanced computational physics research demonstrating expertise in ML engineering, scientific computing, and full-stack development. For collaboration, licensing, or employment inquiries, please get in touch.*