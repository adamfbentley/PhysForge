from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime

# --- JWT related schemas (from Auth Service) ---
# Re-use from Job Orchestration Service for consistency
class TokenData(BaseModel):
    email: Optional[str] = None

class RoleBase(BaseModel):
    name: str

class Role(RoleBase):
    id: int
    class Config:
        from_attributes = True

class User(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    roles: List[Role] = []
    token: str # Original JWT token for authenticating with other services
    class Config:
        from_attributes = True

# --- Feature Engineering Schemas (STORY-303) ---
class FeatureLibraryConfig(BaseModel):
    polynomial_degree: int = Field(1, ge=0, description="Maximum polynomial degree for features.")
    include_independent_variables: bool = Field(True, description="Include independent variables as features.")
    include_dependent_variable: bool = Field(True, description="Include the dependent variable (u) as a feature.")
    include_derivatives: bool = Field(True, description="Include computed derivatives as features.")
    cross_product_degree: int = Field(1, ge=0, description="Maximum degree for cross-product features (e.g., u*du/dx is degree 2). Set to 1 for no cross-products.")

# --- Derivative & Feature Service Schemas (STORY-301, STORY-302) ---
class OutputGridConfig(BaseModel):
    independent_variables: List[str] = Field(..., description="List of independent variables (e.g., ['x', 't']).")
    grid_resolution: Dict[str, int] = Field(..., description="Resolution for each independent variable (e.g., {'x': 100, 't': 50}).")
    domain_bounds: Dict[str, List[float]] = Field(..., description="Dictionary of min/max bounds for each independent variable (e.g., {'x': [0.0, 1.0], 't': [0.0, 1.0]}).")

class DerivativeJobConfig(BaseModel):
    pinn_model_path: str = Field(..., description="Path to the trained PINN model in object storage (e.g., from pinn-training-results bucket).")
    input_dim: int = Field(..., description="Input dimension of the PINN model.")
    output_dim: int = Field(1, description="Output dimension of the PINN model.")
    network_architecture: Dict[str, Any] = Field(..., description="The network architecture config used for the PINN model (e.g., layers, activation, network_type, fourier_features_scale, branch_layers, trunk_layers, etc.).")
    output_grid: OutputGridConfig = Field(..., description="Configuration for the grid on which derivatives will be computed and exported.")
    max_derivative_order: int = Field(2, ge=1, le=3, description="Maximum order of derivatives to compute (1, 2, or 3). (STORY-301)")
    output_name: str = Field(..., pattern=r'^[a-zA-Z0-9_.-]+$', description="A name for the output derivative results. Must be alphanumeric, underscores, hyphens, or periods (SEC-001).")
    generate_feature_library: bool = Field(False, description="Whether to generate and save a feature library (STORY-303).")
    feature_library_config: Optional[FeatureLibraryConfig] = Field(None, description="Configuration for generating the feature library (STORY-303).")

class DerivativeResult(BaseModel):
    job_id: int = Field(..., description="ID of the job that produced this result.")
    results_path: str = Field(..., description="Path to the saved derivative results (e.g., HDF5) in object storage.")
    logs_path: Optional[str] = Field(None, description="Path to the computation logs in object storage.")
    config_used: Dict[str, Any] = Field(..., description="The full configuration used for this derivative computation run.")
    generated_at: datetime = Field(default_factory=datetime.now, description="Timestamp when the result was generated.")
    feature_library_path: Optional[str] = Field(None, description="Path to the generated feature library HDF5 in object storage (STORY-303).")
