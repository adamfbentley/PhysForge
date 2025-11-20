# Sample Datasets for PhysForge

This directory contains three physics datasets from different regimes to test equation discovery:

## 📁 Available Datasets

### 1. Heat Equation (`sample_heat_equation.csv`)
**Physics:** Diffusion processes, thermal conduction

**Equation:**
```
∂u/∂t = α·∂²u/∂x²
```

**Parameters:**
- α (diffusion coefficient) = 0.01
- Domain: x ∈ [0, 1], t ∈ [0, 1]
- 2,500 data points (50×50 grid)

**Expected Discovery:**
- ✅ Linear second derivative: `u_xx` ≈ +0.01
- ❌ No nonlinear terms
- ❌ No higher-order derivatives

**Generate:**
```bash
python generate_sample_data.py
```

---

### 2. Burgers Equation (`sample_burgers_equation.csv`)
**Physics:** Fluid dynamics, shock waves, traffic flow

**Equation:**
```
∂u/∂t = ν·∂²u/∂x² - u·∂u/∂x
```

**Parameters:**
- ν (viscosity) = 0.01
- Domain: x ∈ [0, 1], t ∈ [0, 2]
- 2,500 data points (50×50 grid)

**Expected Discovery:**
- ✅ Diffusion term: `u_xx` ≈ +0.01
- ✅ Nonlinear convection: `u*u_x` ≈ -1.0
- ❌ No higher-order derivatives

**Significance:** Tests ability to discover **nonlinear** terms!

**Generate:**
```bash
python generate_burgers_data.py
```

---

### 3. Korteweg-de Vries Equation (`sample_kdv_equation.csv`)
**Physics:** Shallow water waves, solitons, plasma physics

**Equation:**
```
∂u/∂t = -α·u·∂u/∂x - β·∂³u/∂x³
```

**Parameters:**
- α (nonlinear coefficient) = 1.0
- β (dispersion coefficient) = 0.01
- Domain: x ∈ [0, 1], t ∈ [0, 0.5]
- 2,500 data points (50×50 grid)

**Expected Discovery:**
- ✅ Nonlinear advection: `u*u_x` ≈ -1.0
- ✅ Third-order dispersion: `u_xxx` ≈ -0.01
- ❌ No second derivatives

**Significance:** Tests ability to discover **third-order** derivatives!

**Special:** Contains a soliton solution - a wave that maintains its shape as it travels.

**Generate:**
```bash
python generate_kdv_data.py
```

---

## 🧪 Testing Strategy

Upload each dataset to PhysForge and verify the discovered equations:

| Dataset | Expected Terms | Physics Type |
|---------|---------------|--------------|
| **Heat** | `u_xx` only | Pure diffusion |
| **Burgers** | `u_xx` + `u*u_x` | Diffusion + Convection |
| **KdV** | `u*u_x` + `u_xxx` | Advection + Dispersion |

### Success Criteria

1. **Correct terms identified** (non-zero coefficients)
2. **Spurious terms rejected** (zero or negligible coefficients)
3. **Coefficient accuracy** (within 10% of true values)
4. **R² score** > 0.95

---

## 📊 Comparison Table

| Property | Heat | Burgers | KdV |
|----------|------|---------|-----|
| **Linearity** | Linear | Nonlinear | Nonlinear |
| **Highest Derivative** | 2nd order | 2nd order | 3rd order |
| **Nonlinear Terms** | None | 1 (`u*u_x`) | 1 (`u*u_x`) |
| **Physical Process** | Diffusion | Diffusion + Shock | Dispersion + Soliton |
| **Solutions** | Smooth decay | Shocks | Traveling waves |

---

## 🔬 Physics Background

### Heat Equation
- Models: Temperature distribution, concentration diffusion
- Real-world: Heat transfer in solids, chemical diffusion
- Solution behavior: Smooth, always diffuses to equilibrium

### Burgers Equation
- Models: Gas dynamics, traffic flow, turbulence
- Real-world: Shock wave formation, highway traffic
- Solution behavior: Can form discontinuities (shocks)
- Connects to: Navier-Stokes equations (1D simplified)

### Korteweg-de Vries Equation
- Models: Shallow water waves, internal waves, plasma oscillations
- Real-world: Ocean waves, tsunami propagation
- Solution behavior: Solitons - stable localized waves
- Historical: First equation with exact multi-soliton solutions

---

## 💡 Tips for Testing

### 1. Start with Heat Equation
- Simplest case - only one term
- Validates basic PINN training works
- Should discover `u_xx ≈ 0.01` with R² > 0.99

### 2. Then Try Burgers
- Tests nonlinear term discovery
- Should find both `u_xx` and `u*u_x`
- Coefficients should be 0.01 and -1.0

### 3. Finally Test KdV
- Most challenging - third derivatives
- Should find `u*u_x` and `u_xxx`
- Validates higher-order derivative computation

### Expected Training Times
- Heat: ~2 minutes
- Burgers: ~2-3 minutes (nonlinear is harder)
- KdV: ~2-3 minutes (higher-order derivatives)

---

## 📝 Notes

- All datasets use periodic boundary conditions
- Grid resolution: 50×50 (sufficient for discovery)
- Time domains chosen to keep solutions stable
- CSV format: `x, t, u` columns

## 🐛 Troubleshooting

**If discovery fails:**
1. Check R² score - should be > 0.90
2. Increase training epochs (try 5,000)
3. Verify CSV format (must have x, t, u columns)
4. Check for NaN values in data

**If wrong terms appear:**
1. Adjust sparsity threshold (default 0.01)
2. Increase sample size for discovery (default 500)
3. Check data quality (smooth derivatives)
