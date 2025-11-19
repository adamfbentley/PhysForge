# Equation Discovery - Technical Details

## What Changed

PhysForge now uses **equation-agnostic discovery** instead of assuming a specific PDE form.

### Before (Limited)
- Assumed heat equation: `u_t = α·u_xx`
- Only discovered one coefficient
- Couldn't detect nonlinear terms

### After (Comprehensive)
- Discovers arbitrary PDEs from library of terms
- Detects linear, nonlinear, and higher-order terms
- Uses sparse regression (SINDy-style approach)

---

## Supported Term Library

### Linear Terms
- `u` - Solution itself
- `u_x` - First spatial derivative (∂u/∂x)
- `u_t` - Time derivative (∂u/∂t) - **This is the target**

### Second Derivatives
- `u_xx` - Second spatial derivative (∂²u/∂x²)
- `u_tt` - Second time derivative (∂²u/∂t²)
- `u_xt` - Mixed derivative (∂²u/∂x∂t)

### Higher Derivatives
- `u_xxx` - Third spatial derivative (∂³u/∂x³)

### Nonlinear Terms
- `u²` - Quadratic term
- `u³` - Cubic term
- `u*u_x` - Convection term (Burgers equation)
- `u*u_xx` - Coupled term
- `u_x²` - Squared gradient

---

## Algorithm Overview

### 1. Data-Driven Training
```python
# Train PINN with minimal physics assumptions
loss = data_loss + 0.001 * smoothness_regularization
```
- Primary objective: Fit the data accurately
- Weak prior: Prefer smooth solutions
- No assumed equation form

### 2. Build Term Library
```python
library = {
    'u': u_values,
    'u_x': computed_derivatives,
    'u_xx': second_derivatives,
    'u²': u_values**2,
    'u*u_x': u_values * u_x_values,
    # ... etc
}
```

### 3. Sparse Regression
```python
# Fit: u_t = c1*u + c2*u_x + c3*u_xx + c4*u² + ...
coeffs = least_squares(library, u_t)

# Threshold small coefficients
coeffs[abs(coeffs) < threshold] = 0
```

### 4. Build Equation
Only keep terms with significant coefficients:
```
u_t = +0.010000*u_xx
```

---

## Examples of Discoverable Equations

### Heat/Diffusion Equation
```
u_t = α·u_xx
```
**Expected terms:** `u_xx` (positive coefficient)

### Burgers Equation
```
u_t = ν·u_xx - u·u_x
```
**Expected terms:** `u_xx` (positive), `u*u_x` (negative)

### Wave Equation (Second-order in time)
```
u_tt = c²·u_xx
```
**Target:** Would need to make `u_tt` the target instead of `u_t`

### Korteweg–de Vries (KdV)
```
u_t = α·u_xxx + β·u·u_x
```
**Expected terms:** `u_xxx`, `u*u_x`

### Reaction-Diffusion
```
u_t = α·u_xx + β·u - γ·u²
```
**Expected terms:** `u_xx`, `u`, `u²`

---

## Current Limitations

### 1. Single Field Only
- Current: `u(x,t)`
- Cannot discover coupled systems like:
  - `u_t = f(u, v, ...)`
  - `v_t = g(u, v, ...)`

### 2. 1D Spatial + Time
- Current: `(x, t) → u`
- For 2D/3D physics, would need:
  - `(x, y, t) → u`
  - Terms: `u_yy`, `u_xy`, etc.

### 3. Assumes `u_t` on Left-Hand Side
- Always solves for `u_t = ...`
- Wave equations with `u_tt` need modification

### 4. Sparsity Threshold
- Fixed at 1% of max coefficient
- Some equations need adaptive thresholding

---

## How It Works Technically

### Automatic Differentiation
```python
u = model(x, t)  # Forward pass
u_x = ∂u/∂x     # Automatic differentiation
u_xx = ∂²u/∂x²  # Chain rule
```

### Least Squares with Normalization
```python
# Normalize columns (different scales)
X_norm = X / std(X)

# Fit normalized
coeffs_norm = (X_norm.T @ X_norm)^(-1) @ X_norm.T @ y

# Un-normalize
coeffs = coeffs_norm / std(X)
```

### Sparsity via Thresholding
```python
max_coeff = max(abs(coeffs))
coeffs[abs(coeffs) < 0.01 * max_coeff] = 0
```

---

## Performance

### Computational Cost
- **Training:** ~60-120 seconds (3000 epochs, CPU)
- **Discovery:** ~2-5 seconds (500 samples, 12 terms)
- **Total:** ~2 minutes end-to-end

### Memory Usage
- Feature matrix: `500 × 12` floats (~24 KB)
- Model parameters: ~2,200 parameters (~9 KB)
- Minimal memory footprint

---

## Future Enhancements

### 1. Adaptive Library
- Auto-detect relevant terms based on data
- Add trigonometric terms for periodic solutions

### 2. Multi-Field Discovery
- Coupled systems: `[u, v, w]`
- Example: Lotka-Volterra, Navier-Stokes

### 3. Iterative Refinement
- Discover → Retrain with physics loss → Discover again
- Sequential Thresholded Least Squares (STRidge)

### 4. Symbolic Simplification
- Use SymPy to simplify discovered equations
- Factor common terms: `u·(u_x + u_xx)`

### 5. Uncertainty Quantification
- Bootstrap sampling for coefficient confidence intervals
- Bayesian sparse regression

---

## References

- **SINDy:** Brunton et al., "Discovering governing equations from data by sparse identification of nonlinear dynamical systems" (PNAS 2016)
- **PINNs:** Raissi et al., "Physics-informed neural networks" (JCP 2019)
- **PDE-FIND:** Rudy et al., "Data-driven discovery of partial differential equations" (Science Advances 2017)
