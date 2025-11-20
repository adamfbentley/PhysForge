# PhysForge Research Edition

**Focus:** Maximum equation discovery capability with deployable simplicity

## What's Different from Demo?

### Added Research Capabilities:
1. **PySR Symbolic Regression** - Discovers transcendental functions (sin, exp, log)
2. **Model Comparison** - Ranks multiple candidate equations by AIC/BIC
3. **Uncertainty Quantification** - Confidence intervals on coefficients
4. **Advanced PINN Architectures** - Fourier features for high-frequency problems (coming soon)
5. **Active Learning** - Suggests optimal next experiments (coming soon)

### Removed:
- Multi-user authentication (single user)
- SaaS infrastructure complexity
- Audit trails (Git is sufficient)

## Quick Start

### Installation

```bash
# Install PySR (requires Julia)
pip install pysr

# Or use conda (includes Julia)
conda install -c conda-forge pysr

# Install other dependencies
pip install -r requirements.txt
```

### Run Locally

```bash
cd app_research
python app.py

# Open browser to http://localhost:8000
```

### Deploy to Render

Same as demo, but with larger instance for PySR:

1. Use `render.yaml` configuration
2. Select **Starter** instance ($7/month) instead of free tier
3. PySR requires more CPU/memory for symbolic regression

## Features

### 1. Sparse Regression (Fast, Linear Terms Only)
- Discovery time: 60-90 seconds
- Finds: Linear combinations of derivatives
- Example: `u_t = 0.01·u_xx`

### 2. PySR Symbolic Regression (Slower, All Functions)
- Discovery time: 2-5 minutes
- Finds: Non-polynomial terms (sin, exp, log, sqrt)
- Example: `u_t = 0.01·u_xx + 0.5·u·(1 - 0.1·u)` (logistic growth)

### 3. Model Comparison
- Ranks equations by AIC/BIC
- Shows R², RMSE, complexity
- Recommends simplest model with good fit

### 4. Uncertainty Quantification
- 95% confidence intervals on coefficients
- Sensitivity analysis
- Helps assess equation reliability

## Example Workflows

### Basic Discovery (Sparse Regression)
```python
# Upload CSV with columns: x, t, u
# Results in 60-90 seconds
# Best for: Standard PDEs (heat, wave, Burgers)
```

### Advanced Discovery (PySR)
```python
# Enable PySR in settings
# Results in 2-5 minutes
# Best for: Novel PDEs with unknown functional forms
```

### Model Comparison
```python
# Both methods run automatically
# Compare sparse vs symbolic results
# Choose best model based on AIC/BIC
```

## Performance

| Method | Time | Dataset Size | Equation Types |
|--------|------|--------------|----------------|
| Sparse | 60-90s | Up to 10K points | Linear terms only |
| PySR | 2-5min | Up to 10K points | All functions |
| PySR (GPU) | 1-2min | Up to 50K points | All functions |

## Research Applications

### Fluid Dynamics
- Discover turbulence closures from DNS data
- Extract subgrid models from LES simulations

### Climate Science
- Emulate expensive GCMs with symbolic equations
- Find parametrizations from observations

### Materials Science
- Discover constitutive laws from DFT calculations
- Extract phase field models from atomistic simulations

### Biophysics
- Identify reaction-diffusion systems from microscopy
- Discover cellular dynamics equations

## Publications

If you use PhysForge Research Edition in your work, please cite:

```bibtex
@software{physforge2025,
  title={PhysForge: Automated PDE Discovery with Symbolic Regression},
  author={Bentley, Adam},
  year={2025},
  url={https://github.com/adamfbentley/PhysForge}
}
```

## Comparison to Existing Tools

| Feature | PhysForge Research | PySINDy | AI Feynman | DeepXDE |
|---------|-------------------|---------|------------|---------|
| Sparse Regression | ✅ | ✅ | ❌ | ❌ |
| Symbolic (PySR) | ✅ | ❌ | ✅ | ❌ |
| Model Comparison | ✅ | ⚠️ Basic | ❌ | ❌ |
| Uncertainty Quantification | ✅ | ⚠️ Bootstrap only | ❌ | ❌ |
| PINN Training | ✅ | ❌ | ❌ | ✅ |
| Web Interface | ✅ | ❌ | ❌ | ❌ |
| GPU Support | 🔜 Soon | ❌ | ❌ | ✅ |
| Active Learning | 🔜 Soon | ❌ | ❌ | ❌ |

## Roadmap

### Phase 1 (Complete):
- ✅ Basic sparse regression
- ✅ Web interface with progress tracking
- ✅ Deployed demo

### Phase 2 (Current - 2 weeks):
- 🔄 PySR symbolic regression integration
- 🔄 Model comparison (AIC/BIC ranking)
- 🔄 Uncertainty quantification
- 📋 Fourier feature PINNs

### Phase 3 (4 weeks):
- 📋 Active learning loop
- 📋 GPU acceleration
- 📋 Large dataset support (100K+ points)

### Phase 4 (8 weeks):
- 📋 Multi-fidelity PINNs
- 📋 Ensemble predictions
- 📋 Automated hyperparameter tuning

## Technical Details

### Architecture
```
┌─────────────────┐
│  Web Interface  │
│  (HTML/JS)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   FastAPI App   │
│  - PINN Train   │
│  - Sparse       │
│  - PySR         │
│  - Model Rank   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  SQLite DB      │
│  Local Storage  │
└─────────────────┘
```

### Why This Architecture?

**Deployable:** Single service, minimal infrastructure
**Research-focused:** Maximum discovery capability
**No SaaS bloat:** No auth, no multi-tenancy
**Extensible:** Easy to add GPU, active learning, etc.

## Contributing

This is a research tool, not a SaaS product. Contributions welcome for:
- New equation discovery algorithms
- Better PINN architectures
- Active learning strategies
- Uncertainty quantification methods

Not interested in:
- User authentication systems
- Multi-tenancy features
- Billing/subscription logic
- Admin dashboards

## License

See LICENSE file

## Contact

- GitHub: https://github.com/adamfbentley/PhysForge
- Issues: https://github.com/adamfbentley/PhysForge/issues
