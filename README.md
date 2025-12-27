# PhysForge: Automated PDE Discovery

[![Demo: Live](https://img.shields.io/badge/demo-live-brightgreen.svg)](https://physforge.onrender.com)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

Discover governing equations from spatiotemporal data using Physics-Informed Neural Networks (PINNs) and sparse regression.

**🔗 Live Demo:** https://physforge.onrender.com

---

## Overview

PhysForge automatically discovers partial differential equations from CSV data using physics-informed machine learning. Upload spatiotemporal measurements, train a neural network constrained by physics, and extract the governing equation.

**How it works:**
1. Upload CSV with columns: x (space), t (time), u (field value)
2. PINN trains while satisfying PDE structure
3. Sparse regression identifies equation terms
4. View discovered equation with quality metrics

---

## Quick Start

### Try the Live Demo
Visit https://physforge.onrender.com and upload one of the sample datasets:
- `sample_heat_equation.csv` - Diffusion process
- `sample_burgers_equation.csv` - Nonlinear wave propagation
- `sample_kdv_equation.csv` - Soliton dynamics

### Run Locally
```bash
cd app_simplified
pip install -r requirements.txt
python app.py
```
Visit http://localhost:5000

---

## Technical Details

### Physics-Informed Neural Networks
PyTorch implementation with automatic differentiation:
- Neural network learns field u(x,t) from data
- Physics loss enforces PDE structure: ∂u/∂t = f(u, ∂u/∂x, ∂²u/∂x², ...)
- Network trained on both data fitting and physics constraints

### Equation Discovery
Sparse regression identifies coefficients from neural network derivatives:
1. Compute derivatives using autograd
2. Build library of candidate terms (u, u_x, u_xx, uu_x, etc.)
3. Sparse least-squares finds minimal equation
4. Quality metrics: R², term count, residuals

### Validated Examples
- **Heat equation:** u_t = 0.1·u_xx
- **Burgers equation:** u_t = 0.1·u_xx - u·u_x  
- **KdV equation:** u_t = -u·u_x - u_xxx

---

## Use Cases

- **Research:** Discover PDEs from simulation/experimental data
- **Education:** Demonstrate machine learning for physics
- **Validation:** Test theoretical models against measurements
- **Portfolio:** Full-stack ML engineering showcase

---

## Performance

- Training: 15-25 minutes for 1000 epochs (typical)
- Equation discovery: <5 seconds
- Dataset size: Tested up to 10,000 spatiotemporal points
- Hardware: CPU-optimized (Render free tier)

---

## Related Projects

**PhysForge Research Edition:** Enhanced version with multiple discovery algorithms (SINDy, PySR), uncertainty quantification, and comprehensive benchmarking. Available at [PhysForge_Research](../PhysForge_Research/)

---

## Technical Stack

- **Backend:** Python 3.9+, PyTorch, FastAPI, NumPy, SciPy
- **Frontend:** Vanilla JavaScript, HTML5
- **Deployment:** Docker, Render
- **Database:** SQLite (ephemeral)

---

## Contributing

Issues and suggestions welcome. This is a portfolio/research project demonstrating PINN-based equation discovery.

---

## License

MIT License - See LICENSE file

---

## Contact

**Adam Frank Bentley**
- Email: adam.f.bentley@gmail.com
- GitHub: [@adamfbentley](https://github.com/adamfbentley)
- Live Demo: https://physforge.onrender.com

---

## Acknowledgments

- Raissi et al. (2019) - Physics-Informed Neural Networks
- PyTorch team for automatic differentiation
- SciPy community for numerical optimization
