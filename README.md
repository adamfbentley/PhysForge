# PhysForge

PhysForge is a prototype application for exploring partial-differential-equation
(PDE) discovery from spatiotemporal data. It combines a PyTorch neural surrogate,
automatic differentiation, thresholded least-squares regression, and a FastAPI
interface.

The project is an engineering and learning prototype, not a validated scientific
instrument. Results from noisy, sparse, or experimental data should not be
treated as reliable equation identification without an external benchmark and
uncertainty analysis.

## Method

Given a CSV containing `x`, `t`, and `u`, the application:

1. fits a neural surrogate for `u(x,t)`;
2. evaluates spatial and temporal derivatives with automatic differentiation;
3. constructs a candidate library such as `u`, `u_x`, `u_xx`, and `u*u_x`;
4. uses iterative thresholded least squares to select active terms; and
5. reports coefficients, residual diagnostics, and term-stability estimates.

The implementation is in `app_simplified/app.py`.

## Run locally

```bash
cd app_simplified
python -m pip install -r requirements.txt
python app.py
```

The service starts at `http://localhost:8000`; its health endpoint is
`http://localhost:8000/health`.

## Sample data

The repository includes generated datasets for the heat, Burgers, and KdV
equations. These datasets provide controlled demonstrations with known
generating equations. Their presence does not by itself validate recovery of
the correct terms or coefficients.

No reproducible end-to-end benchmark table is currently published. A scientific
validation should report, over fixed train/test splits and multiple random
seeds:

- field prediction error on held-out points;
- derivative error against known derivatives;
- active-term precision and recall;
- relative coefficient error;
- PDE residual on held-out data; and
- sensitivity to noise, sampling density, and sparsity thresholds.

Until those measurements are recorded, the sample equations should be described
as intended test cases rather than validated recoveries.

## Tests

```bash
python -m pytest -q
```

The test suite covers input validation, selected API and persistence behavior,
and controlled sparse-regression fixtures. It is not a substitute for the
end-to-end PDE-discovery benchmark described above.

## Repository layout

```text
app_simplified/        FastAPI application, discovery pipeline, and sample data
tests/                 Unit and controlled-fixture tests
docs/api.md            API notes
demo_minimal_pinn.py   Standalone heat-equation PINN demonstration
```

## References

- Raissi, Perdikaris, and Karniadakis (2019), Physics-informed neural networks.
- Brunton, Proctor, and Kutz (2016), Sparse identification of nonlinear dynamics.

## License

MIT. See `LICENSE`.
