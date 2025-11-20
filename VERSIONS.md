# PhysForge - Version Guide

This repository contains **four versions** of PhysForge, each serving a different purpose. This guide helps you navigate the codebase.

---

## 📁 Repository Structure

```
PhysForge_-_Meta-Simulation/
├── app_simplified/          # Version 1: Demo (DEPLOYED ✅)
├── app_research/            # Version 2: Research Prototype (Legacy)
├── backend/                 # Version 3: Production Platform (Untested)
├── frontend/                # Frontend for Production Platform
├── docs/                    # General documentation
├── tests/                   # Cross-version tests
└── VERSIONS.md             # This file
```

**Separate Repository:**
```
PhysForge_Research/          # Version 4: Standalone Research Edition (TESTED ✅)
```

---

## Version Comparison

| Version | Location | Status | Lines | Purpose |
|---------|----------|--------|-------|---------|
| **1. Demo** | `app_simplified/` | ✅ Deployed | ~500 | Quick proof-of-concept |
| **2. Research (old)** | `app_research/` | ⚠️ Prototype | ~800 | Early research version |
| **3. Production** | `backend/` | ❌ Untested | ~15K | Enterprise platform |
| **4. Research (new)** | `../PhysForge_Research/` | ✅ Tested | ~2K | Validated research tool |

---

## Version Details

### 1. Demo Application (`app_simplified/`)

**Status:** ✅ **DEPLOYED & WORKING**  
**URL:** https://physforge.onrender.com  
**File:** Single `app.py` (~500 lines)

**What it does:**
- Upload CSV → Train PINN → Discover equation
- Sparse regression only (no PySR)
- Real-time progress logs
- SQLite database

**Use for:**
- Quick demonstrations
- Teaching PINNs
- Portfolio showcase
- Linear PDE discovery

**Limitations:**
- Can't find nonlinear terms (sin, exp, log)
- Single user at a time
- CPU only

**Deployment:**
```bash
cd app_simplified
python app.py
# Visit http://localhost:8000
```

---

### 2. Research Prototype (`app_research/`)

**Status:** ⚠️ **LEGACY** - Superseded by PhysForge_Research  
**Files:** `app.py`, `pysr_discovery.py`, `model_comparison.py`, `uncertainty.py`

**What it has:**
- PySR symbolic regression integration
- Basic model comparison
- Uncertainty quantification stubs
- Enhanced web interface

**Why it exists:**
- Proof-of-concept for PySR integration
- Basis for standalone research edition
- Shows evolution from demo to research tool

**Current state:**
- Never fully tested
- Some features incomplete
- Used as reference for PhysForge_Research

**Use for:**
- Reference implementation
- Understanding design evolution
- Extracting specific features

**Note:** For actual research work, use `PhysForge_Research/` instead.

---

### 3. Production Platform (`backend/` + `frontend/`)

**Status:** ❌ **UNTESTED** - Architecture complete, needs validation  
**Files:** 104 Python files, 10 microservices

**Architecture:**
```
backend/
├── auth_service/              # JWT authentication, RBAC
├── data_management_service/   # Dataset upload, MinIO storage
├── job_orchestration_service/ # Redis Queue, job lifecycle
├── pinn_training_service/     # PINN training workers
├── derivative_feature_service/# Derivative computation
├── pde_discovery_service/     # SINDy + PySR integration
├── active_experiment_service/ # Adaptive sampling
├── reporting_service/         # Generate reports
├── audit_service/             # Audit logging
└── cli_service/               # Command-line interface

frontend/
├── src/
│   ├── components/            # React components
│   ├── services/              # API clients
│   └── pages/                 # Main pages
└── package.json
```

**What it does (when integrated):**
- Multi-user authentication (JWT + RBAC)
- Dataset versioning with metadata
- Background job processing (Redis Queue)
- GPU cluster support
- Active learning module
- Audit logging for compliance
- REST API with OpenAPI docs

**Use for:**
- Commercial SaaS platform
- Enterprise deployment
- Multi-tenant applications
- High-throughput research facilities

**Requirements:**
- PostgreSQL (per-service databases)
- Redis (job queue)
- MinIO/S3 (object storage)
- Docker Compose or Kubernetes
- 2-3 months integration testing

**Deployment:**
```bash
docker-compose up -d
# Requires: docker-compose.yml, environment setup
```

---

### 4. Standalone Research Edition (`../PhysForge_Research/`)

**Status:** ✅ **TESTED & VALIDATED** (93.3% test pass rate)  
**Location:** Separate repository/directory

**What it has:**
- Unified discovery engine (468 lines)
- Model comparison framework (417 lines)
- Uncertainty quantification (417 lines)
- Integration test suite (348 lines)
- 7 benchmark PDE datasets
- Comprehensive documentation

**Architecture:**
```
PhysForge_Research/
├── discovery_engine.py        # Main orchestrator
├── model_comparison.py        # AIC/BIC ranking
├── uncertainty.py             # Bootstrap CI, sensitivity
├── pysr_discovery.py          # PySR wrapper
├── app.py                     # Web interface
├── tests/
│   └── test_integration.py   # 15 integration tests
├── data/examples/             # 7 benchmark datasets
├── quickstart_example.py      # Working demo
├── CRITICAL_ANALYSIS.md       # Issue identification
├── TEST_REPORT.md             # Validation results
└── STATUS_REPORT.md           # Complete status
```

**Use for:**
- Academic research papers
- Discovering complex equations
- Comparing discovery methods
- Uncertainty quantification
- Systematic benchmarking

**Advantages:**
1. **Tested:** 93.3% pass rate (14/15 tests)
2. **Modular:** Clean separation of concerns
3. **Documented:** Comprehensive analysis + test reports
4. **No bloat:** Zero auth/multi-tenant code
5. **Fast:** 5s discovery on 1200 points

**Deployment:**
```bash
cd PhysForge_Research
pip install -r requirements.txt
python quickstart_example.py  # Test it
python app.py                  # Web interface
```

---

## Decision Guide

### "I want to see how PhysForge works (5 minutes)"
→ **Use Version 1 (Demo)** - Visit https://physforge.onrender.com

### "I'm writing a research paper"
→ **Use Version 4 (Research - new)** - Test locally with quickstart

### "I'm building a commercial SaaS product"
→ **Use Version 3 (Production)** - Budget 2-3 months for testing

### "I need to reference old research prototype"
→ **See Version 2 (Research - old)** - For historical context only

---

## Migration Paths

**From Demo → Research:**
```bash
# Demo limitations revealed
cd ../PhysForge_Research
python quickstart_example.py  # Test with your data
```

**From Research (old) → Research (new):**
```bash
# Already migrated! Old version kept for reference
cd ../PhysForge_Research  # Use this instead
```

**From Research → Production:**
```bash
# When you need multi-user support
cd backend
docker-compose up -d  # After 2-3 months integration work
```

---

## GitHub Organization

### Main Repository: `PhysForge_-_Meta-Simulation/`

**README.md** explains all versions with links  
**VERSIONS.md** (this file) - Navigation guide  
**VERSION_COMPARISON.md** - Detailed feature comparison  

**Branches:**
- `main` - All four versions coexist
- `demo-only` - Just app_simplified/ (optional)
- `production-dev` - Backend development (optional)

### Separate Repository: `PhysForge_Research/`

**Why separate?**
- Clean slate for research
- Independent versioning
- Focused on research value
- Easier to share with collaborators
- Can be cited independently

**README.md** research-focused  
**Citation:** Includes BibTeX  
**Comparison:** Shows advantages vs PySINDy/AI Feynman

---

## File Counts

| Version | Python Files | Total Lines | Key Files |
|---------|--------------|-------------|-----------|
| Demo | 1 | 594 | app.py |
| Research (old) | 4 | ~800 | app.py, pysr_discovery.py |
| Production | 104 | ~15,000 | 10 services × ~10 files each |
| Research (new) | 8 | ~2,000 | discovery_engine.py, tests/ |

---

## Quick Reference

**Want to deploy something today?**
- Demo: Already deployed at physforge.onrender.com
- Research (new): `pip install -r requirements.txt && python app.py`

**Want to publish a paper?**
- Use Research (new): Tested, validated, citable

**Want to build a startup?**
- Start with Research (new), migrate to Production after funding

**Want to understand the evolution?**
- Read: Demo → Research (old) → Research (new) + Production (parallel)

---

## Questions?

**"Which version should I use?"**  
→ See decision guide above

**"Why so many versions?"**  
→ Evolution: Demo (proof) → Research (novel) → Production (scale)

**"Can I delete old versions?"**  
→ Keep all for reference, but only maintain Demo + Research (new)

**"Where's the latest code?"**  
→ Demo: app_simplified/app.py (deployed)  
→ Research: ../PhysForge_Research/ (tested)

---

## Last Updated

**Date:** November 21, 2025  
**Active Versions:** Demo (deployed), Research new (tested)  
**In Development:** Production (needs 2-3 months)  
**Deprecated:** Research old (use new version instead)
