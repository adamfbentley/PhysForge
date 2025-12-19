# PhysForge: Physics-Informed Neural Network Discovery Platform

[![Demo: Live](https://img.shields.io/badge/demo-live-brightgreen.svg)](https://physforge.onrender.com)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![React 18](https://img.shields.io/badge/react-18-blue.svg)](https://reactjs.org/)

Automated discovery of governing equations from spatiotemporal data using Physics-Informed Neural Networks (PINNs) and sparse regression.

**Live Demo:** https://physforge.onrender.com

---

## Overview

PhysForge combines physics-informed machine learning with symbolic regression to automatically discover partial differential equations from experimental or simulation data. Upload CSV data, train a physics-aware neural network, and extract the governing equations.

**Current Status:**
- **Demo Application:** Deployed and functional at physforge.onrender.com
- **Microservices Platform:** Architecture designed, individual services implemented, integration in progress
- **Research Edition:** Separate repository with enhanced validation and benchmarking

---

## Project Structure

This repository contains three versions optimized for different use cases:

### 1. Demo Application ✅ DEPLOYED
**Location:** `app_simplified/` | **Live:** https://physforge.onrender.com

Single-service application demonstrating core PINN training and sparse equation discovery workflow.

**Features:**
- CSV data upload for spatiotemporal datasets
- Physics-Informed Neural Network training with automatic differentiation
- Sparse regression for equation discovery
- Real-time progress tracking
- Complete workflow in <90 seconds on CPU

**Technical Stack:** Python, PyTorch, FastAPI, NumPy, SciPy

**Deployment:** Docker container on Render free tier

**Use Case:** Quick demonstrations, teaching, portfolio showcase, testing on simple PDEs

---

### 2. Microservices Platform 🚧 IN DEVELOPMENT
**Location:** `backend/` + `frontend/`

Production-oriented architecture with independent services for scalability and maintainability.

**Architecture:**
- 10 FastAPI microservices (Auth, Data Management, Job Orchestration, PINN Training, Derivatives, PDE Discovery, Active Learning, Reporting, CLI, Audit)
- React 18 + TypeScript frontend with Mantine UI
- PostgreSQL per-service with SQLAlchemy ORM
- Redis + RQ for asynchronous job processing
- MinIO for S3-compatible object storage
- Prometheus + Grafana monitoring stack

**Current State:**
- Individual services implemented with FastAPI
- Frontend components built with full type safety
- Database schemas designed
- Docker Compose orchestration configured
- Integration testing in progress

**Use Case:** Multi-user platforms, enterprise deployment, commercial SaaS applications

---

### 3. Research Edition 📊 SEPARATE REPOSITORY
**Location:** `../PhysForge_Research/`

Enhanced version focused on research validation, benchmarking, and advanced algorithms.

**Additional Features:**
- Unified discovery engine (PINN + SINDy + PySR)
- Model comparison with AIC/BIC ranking
- Uncertainty quantification with bootstrap confidence intervals
- Comprehensive test suite (14/15 tests passing)
- 7 benchmark PDE datasets

**Use Case:** Research publications, complex equations, systematic benchmarking

---

## Quick Start

### Try the Live Demo
Visit https://physforge.onrender.com and upload CSV data with columns: x, t, u (spatial coordinate, time, field value)

### Run Demo Locally
```bash
cd app_simplified
pip install -r requirements.txt
python app.py
```
Visit http://localhost:5000

### Development Setup
```bash
# Clone repository
git clone https://github.com/adamfbentley/PhysForge.git
cd PhysForge

# For microservices platform
docker-compose up
```

---

## Technical Implementation

### Physics-Informed Neural Networks
Custom PyTorch implementation enforcing PDE constraints through physics-informed loss:
- Automatic differentiation for computing derivatives
- Physics constraints incorporated in loss function
- Support for 1st, 2nd, and 3rd order derivatives
- Multiple network architectures (MLP, Fourier Features, DeepONet)

### Equation Discovery
Sparse regression identifies governing equations from learned derivatives:
- Library-based approach testing candidate terms
- Least-squares optimization for coefficient fitting
- Support for linear and nonlinear PDEs
- Extensible to symbolic regression (PySR) in research edition

### Validated Test Cases
- Heat equation: ∂u/∂t = ν∇²u
- Burgers equation: ∂u/∂t = ν∇²u - u∂u/∂x
- KdV equation: ∂u/∂t = -u∂u/∂x - ∂³u/∂x³

---

## Applications

**Scientific Computing:**
- Discover governing equations from fluid dynamics simulations
- Extract PDEs from climate and weather data
- Reverse-engineer physical models from experimental measurements

**Research:**
- Automated equation discovery reducing weeks of analysis to minutes
- Systematic exploration of parameter spaces
- Validation of theoretical models against data

**Education:**
- Teaching PINNs and scientific machine learning
- Demonstrating equation discovery workflows
- Hands-on experimentation with real algorithms

---

## Development Roadmap

**Completed:**
- ✅ Core PINN implementation with PyTorch
- ✅ Sparse regression equation discovery
- ✅ Demo application deployment
- ✅ Microservices architecture design
- ✅ React frontend implementation
- ✅ Monitoring stack configuration

**In Progress:**
- 🚧 Microservices integration testing
- 🚧 Authentication and multi-user support
- 🚧 Advanced visualization (3D plotting, interactive charts)
- 🚧 Real-time WebSocket updates

**Planned:**
- 📋 GPU acceleration support
- 📋 Active learning for optimal data sampling
- 📋 Mobile-responsive interface improvements
- 📋 Extended PDE library and benchmarks

---

## Documentation

- **README.md** - Project overview (this file)
- **VERSIONS.md** - Detailed guide to all versions
- **VERSION_COMPARISON.md** - Feature comparison table
- **architecture.md** - System architecture and design decisions
- **CURRENT_STATUS.md** - Implementation status by component
- **docs/api.md** - API endpoint documentation

---

## Performance

**Demo Application:**
- Training: 30-60 seconds for typical datasets (10,000 points)
- Equation discovery: <5 seconds
- Total workflow: <90 seconds on CPU
- Memory: ~500 MB peak usage

**Scalability:**
- Tested on datasets up to 10,000 spatiotemporal points
- Supports 1D+time problems
- CPU-based computation (GPU support planned)

---

## Contributing

Contributions welcome. Please open issues for bugs or feature requests. Pull requests should include tests and documentation updates.

---

## License

Proprietary - Personal Project

---

## Contact

**Adam Frank Bentley**
- Email: adam.f.bentley@gmail.com
- GitHub: github.com/adamfbentley
- Demo: https://physforge.onrender.com

---

## Acknowledgments

Built using:
- PyTorch for automatic differentiation and neural networks
- FastAPI for REST API services
- React 18 for modern web interface
- Docker for containerization
- Research inspired by Raissi et al. (2019) on Physics-Informed Neural Networks
