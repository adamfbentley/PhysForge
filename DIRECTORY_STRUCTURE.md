# PhysForge - Directory Structure

This document explains the organization of all PhysForge versions.

---

## 📁 Workspace Layout

```
pp/                                      # Your workspace root
│
├── PhysForge_-_Meta-Simulation/        # Main repository (4 versions)
│   ├── app_simplified/                 # ✅ Version 1: Demo (deployed)
│   │   ├── app.py                      # Single-file application (594 lines)
│   │   ├── static/                     # Web interface files
│   │   ├── uploads/                    # User uploads
│   │   ├── results/                    # Generated plots
│   │   └── physforge.db               # SQLite database
│   │
│   ├── app_research/                   # ⚠️ Version 2: Research prototype (legacy)
│   │   ├── app.py                      # Main web app
│   │   ├── pysr_discovery.py          # PySR integration
│   │   ├── model_comparison.py        # Comparison framework
│   │   ├── uncertainty.py             # UQ stubs
│   │   └── static/                     # Enhanced UI
│   │
│   ├── backend/                        # ❌ Version 3: Production platform (untested)
│   │   ├── auth_service/              # JWT authentication
│   │   ├── data_management_service/   # Dataset management
│   │   ├── job_orchestration_service/ # Redis Queue
│   │   ├── pinn_training_service/     # PINN workers
│   │   ├── derivative_feature_service/# Derivatives
│   │   ├── pde_discovery_service/     # SINDy + PySR
│   │   ├── active_experiment_service/ # Active learning
│   │   ├── reporting_service/         # Reports
│   │   ├── audit_service/             # Audit logs
│   │   ├── cli_service/               # CLI interface
│   │   ├── shared/                    # Shared utilities
│   │   └── tests/                     # Service tests
│   │
│   ├── frontend/                       # React UI for production
│   │   ├── src/
│   │   │   ├── components/            # React components
│   │   │   ├── services/              # API clients
│   │   │   └── pages/                 # Page components
│   │   └── package.json
│   │
│   ├── docs/                           # Documentation
│   │   ├── architecture.md            # System architecture
│   │   ├── api/                       # API documentation
│   │   └── guides/                    # User guides
│   │
│   ├── tests/                          # Cross-service tests
│   │
│   ├── README.md                       # Main overview (you are here)
│   ├── VERSIONS.md                     # Version navigation guide
│   ├── VERSION_COMPARISON.md           # Detailed comparison
│   ├── DIRECTORY_STRUCTURE.md          # This file
│   ├── SCOPE_AND_VISION.md            # Strategic overview
│   ├── architecture.md                # Technical architecture
│   ├── docker-compose.yml             # Multi-service orchestration
│   └── .gitignore
│
└── PhysForge_Research/                 # ✅ Version 4: Standalone research (tested)
    ├── discovery_engine.py             # Main orchestrator (468 lines)
    ├── model_comparison.py             # AIC/BIC ranking (417 lines)
    ├── uncertainty.py                  # Bootstrap UQ (417 lines)
    ├── pysr_discovery.py               # PySR wrapper (208 lines)
    ├── app.py                          # Web interface (594 lines)
    │
    ├── tests/                          # Testing suite
    │   └── test_integration.py         # 15 integration tests
    │
    ├── data/                           # Data directory
    │   └── examples/                   # Benchmark datasets
    │       ├── heat_equation.csv
    │       ├── burgers_equation.csv
    │       ├── reaction_diffusion.csv
    │       ├── kdv_equation.csv
    │       ├── wave_equation.csv
    │       ├── allen_cahn.csv
    │       └── advection_diffusion.csv
    │
    ├── results/                        # Generated results
    │   ├── plots/
    │   ├── models/
    │   └── reports/
    │
    ├── static/                         # Web UI files
    ├── uploads/                        # User uploads
    │
    ├── quickstart_example.py           # Working demonstration
    ├── generate_benchmarks.py          # Generate test data
    │
    ├── README.md                       # Research-focused README
    ├── QUICKSTART.md                   # Getting started guide
    ├── CRITICAL_ANALYSIS.md            # Issue identification
    ├── TEST_REPORT.md                  # Validation results
    ├── STATUS_REPORT.md                # Complete status
    ├── DATASETS.md                     # Benchmark documentation
    ├── EQUATION_DISCOVERY.md           # Algorithm explanation
    ├── DEPLOYMENT.md                   # Deployment guide
    │
    ├── requirements.txt                # Python dependencies
    ├── .gitignore                      # Research-focused ignores
    └── render.yaml                     # Render.com deployment
```

---

## File Organization Principles

### PhysForge_-_Meta-Simulation/ (Main Repository)

**Purpose:** Historical evolution showing all versions and architectures

**Organization:**
- `app_*/` - Complete applications (self-contained)
- `backend/` - Microservices (service-per-directory)
- `frontend/` - React UI (standard React structure)
- `docs/` - Cross-version documentation
- `tests/` - Integration tests
- Root-level `.md` files - Navigation and overview

**Git Strategy:**
- Main branch has all versions
- Tag releases: `v1.0-demo`, `v2.0-research-proto`, `v3.0-production`
- Keep history to show evolution

---

### PhysForge_Research/ (Standalone Repository)

**Purpose:** Clean, tested research tool for papers and reproducibility

**Organization:**
- Core modules at root (discovery_engine.py, etc.)
- `tests/` - Comprehensive test suite
- `data/examples/` - Reproducible benchmarks
- `results/` - Generated outputs (gitignored)
- Root-level `.md` files - Research-focused docs

**Git Strategy:**
- Separate repository for clean history
- Semantic versioning: v1.0.0, v1.1.0, etc.
- Tagged releases for paper citations
- No legacy code

---

## Key Files by Purpose

### "I want to run PhysForge now"

**Demo:**
```
PhysForge_-_Meta-Simulation/app_simplified/app.py
```
Visit: https://physforge.onrender.com

**Research (local):**
```
PhysForge_Research/quickstart_example.py
PhysForge_Research/app.py
```

---

### "I want to understand the code"

**Simple implementation:**
```
PhysForge_-_Meta-Simulation/app_simplified/app.py       # 594 lines, all logic
```

**Modular implementation:**
```
PhysForge_Research/discovery_engine.py                   # Main pipeline
PhysForge_Research/model_comparison.py                   # Comparison
PhysForge_Research/uncertainty.py                        # UQ
```

**Microservices architecture:**
```
PhysForge_-_Meta-Simulation/architecture.md              # Overview
PhysForge_-_Meta-Simulation/backend/*/main.py           # Each service
```

---

### "I want to test it"

**Integration tests:**
```
PhysForge_Research/tests/test_integration.py            # Run with: python tests/test_integration.py
```

**Quickstart validation:**
```
PhysForge_Research/quickstart_example.py                # Run with: python quickstart_example.py
```

**Service tests:**
```
PhysForge_-_Meta-Simulation/backend/*/tests/           # pytest test_*.py
```

---

### "I want to deploy it"

**Demo (already deployed):**
```
PhysForge_-_Meta-Simulation/app_simplified/render.yaml
```

**Research (deploy to Render):**
```
PhysForge_Research/render.yaml
PhysForge_Research/DEPLOYMENT.md
```

**Production (Docker Compose):**
```
PhysForge_-_Meta-Simulation/docker-compose.yml
PhysForge_-_Meta-Simulation/backend/*/Dockerfile
```

---

### "I want to understand the strategy"

**Overall vision:**
```
PhysForge_-_Meta-Simulation/SCOPE_AND_VISION.md
PhysForge_-_Meta-Simulation/architecture.md
```

**Version navigation:**
```
PhysForge_-_Meta-Simulation/VERSIONS.md
PhysForge_-_Meta-Simulation/VERSION_COMPARISON.md
```

**Research edition status:**
```
PhysForge_Research/STATUS_REPORT.md
PhysForge_Research/CRITICAL_ANALYSIS.md
PhysForge_Research/TEST_REPORT.md
```

---

## GitHub Repository Structure

### Repository: `PhysForge` (Main)

**README.md** - Overview linking to all versions  
**VERSIONS.md** - Navigation guide  
**Branches:**
- `main` - All versions coexist
- `demo` - Only app_simplified/ (optional)
- `production-dev` - Backend development (optional)

---

### Repository: `PhysForge-Research` (Separate)

**README.md** - Research-focused, includes citation  
**No legacy code** - Clean repository  
**Tagged releases** - v1.0.0, v1.1.0 for citations  

---

## Ignored Files (Git)

### PhysForge_-_Meta-Simulation/.gitignore
```
__pycache__/
*.pyc
.env
*.db
*.sqlite
app_simplified/uploads/
app_simplified/results/
app_research/uploads/
app_research/results/
backend/*/logs/
frontend/node_modules/
frontend/build/
```

### PhysForge_Research/.gitignore
```
__pycache__/
*.pyc
.env
*.db
physforge.db
data/raw/              # Keep examples/
results/               # All results gitignored
uploads/
logs/
models/checkpoints/    # Keep models/ structure
static/uploads/
*.log
```

---

## Navigation Tips

### "Where's the latest working code?"

**Deployed demo:**
```
PhysForge_-_Meta-Simulation/app_simplified/app.py
```

**Tested research tool:**
```
PhysForge_Research/discovery_engine.py
```

### "Where are the tests?"

**Research edition:**
```
PhysForge_Research/tests/test_integration.py     # 93.3% pass
```

**Production services:**
```
PhysForge_-_Meta-Simulation/backend/*/tests/     # Various coverage
```

### "Where's the documentation?"

**Getting started:**
```
PhysForge_-_Meta-Simulation/README.md
PhysForge_Research/QUICKSTART.md
```

**Technical details:**
```
PhysForge_-_Meta-Simulation/architecture.md
PhysForge_Research/EQUATION_DISCOVERY.md
```

**Status reports:**
```
PhysForge_Research/STATUS_REPORT.md              # Current state
PhysForge_Research/TEST_REPORT.md                # Validation
```

---

## Maintenance Strategy

### Active Development
- **Demo:** Maintenance only (deployed, working)
- **Research (new):** Active development for papers
- **Production:** On hold (needs 2-3 months)

### Updates
- Demo: Bug fixes only
- Research: New features, accuracy improvements
- Production: Architecture planning

### Testing
- Demo: Manual testing before deploy
- Research: Run `python tests/test_integration.py` before commits
- Production: Needs full integration test suite

---

## Summary

**Two main directories:**
1. `PhysForge_-_Meta-Simulation/` - Evolution and history (4 versions)
2. `PhysForge_Research/` - Clean research tool (tested)

**For most users:**
- Start with demo: https://physforge.onrender.com
- Use for research: `PhysForge_Research/`
- Reference old versions: `PhysForge_-_Meta-Simulation/app_research/`
- Production planning: `PhysForge_-_Meta-Simulation/backend/`

**Well organized:**
- ✅ Clear separation of versions
- ✅ Comprehensive documentation
- ✅ Easy navigation with VERSIONS.md
- ✅ Clean research repository
- ✅ Historical evolution preserved
