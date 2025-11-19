from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime

# --- JWT related schemas (from Auth Service) ---
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

# --- PDE Discovery Service Schemas (STORY-401, STORY-402, STORY-403, STORY-404, STORY-405, STORY-501, STORY-502, STORY-503, STORY-504) ---

class SindyConfig(BaseModel):
    optimizer: Literal["STLSQ", "SR3"] = Field("STLSQ", description="SINDy optimizer.")
    threshold: float = Field(0.01, description="Sparsity threshold for SINDy.")
    alpha: float = Field(0.05, description="Regularization parameter for SR3 (if used).")
    max_iter: int = Field(20, description="Maximum iterations for SINDy optimizer.")
    # STORY-404: Cross-validation
    cross_validation_folds: Optional[int] = Field(None, ge=2, description="Number of folds for cross-validation. If None, no cross-validation.")
    # STORY-405: Uncertainty Quantification
    uncertainty_quantification_method: Optional[Literal["bootstrap"]] = Field(None, description="Method for uncertainty quantification (e.g., 'bootstrap').")
    bootstrap_samples: int = Field(100, ge=10, description="Number of bootstrap samples for uncertainty quantification.")

class PySRConfig(BaseModel):
    populations: int = Field(10, description="Number of populations for PySR.")
    n_features_to_test: int = Field(10, description="Number of features to test in each iteration.")
    binary_operators: List[str] = Field(["+", "-", "*", "/"], description="Binary operators for PySR.")
    unary_operators: List[str] = Field(["sqrt", "log", "exp", "sin", "cos"], description="Unary operators for PySR.")
    complexity_of_operators: Dict[str, float] = Field({}, description="Complexity of operators for PySR.")
    max_depth: int = Field(5, description="Maximum depth of the symbolic expression tree.")
    timeout_in_seconds: int = Field(60, description="Timeout for PySR in seconds.")
    procs: Optional[int] = Field(None, description="Number of processes to use for PySR. Defaults to number of CPU cores if None.")
    # STORY-404: Cross-validation (PySR has internal validation, but we can expose a flag)
    perform_validation: bool = Field(True, description="Whether to perform internal validation during PySR search.")
    # STORY-405: Uncertainty Quantification (PySR provides confidence intervals, or we can bootstrap)
    uncertainty_quantification_method: Optional[Literal["bootstrap"]] = Field(None, description="Method for uncertainty quantification (e.g., 'bootstrap').")
    bootstrap_samples: int = Field(100, ge=10, description="Number of bootstrap samples for uncertainty quantification.")


class PDEDiscoveryConfig(BaseModel):
    derivative_results_path: str = Field(..., description="Path to the HDF5 file containing computed derivatives and features (from Derivative & Feature Service).")
    target_variable: str = Field(..., description="The dependent variable derivative to discover the PDE for (e.g., 'du_dt', 'd2u_dx2').")
    independent_variables: List[str] = Field(..., description="List of independent variables (e.g., ['x', 't']).")
    dependent_variable: str = Field(..., description="The main dependent variable (e.g., 'u').")
    candidate_features: List[str] = Field(..., description="List of candidate feature names to use for PDE discovery (e.g., ['u', 'du_dx', 'u*du_dx']).")
    discovery_algorithm: Literal["SINDy", "PySR"] = Field(..., description="Algorithm to use for PDE discovery.")
    sindy_config: Optional[SindyConfig] = Field(None, description="Configuration for SINDy algorithm.")
    pysr_config: Optional[PySRConfig] = Field(None, description="Configuration for PySR algorithm.")
    output_name: str = Field(..., description="A name for the output PDE discovery results.")
    # STORY-503: Symbolic manipulation and canonicalization
    canonicalize_equation: bool = Field(True, description="Whether to canonicalize the discovered equation using SymPy.")
    # STORY-504: Sensitivity Analysis
    perform_sensitivity_analysis: bool = Field(False, description="Whether to perform sensitivity analysis on the discovered PDE.")
    sensitivity_analysis_config: Optional[Dict[str, Any]] = Field(None, description="Configuration for sensitivity analysis (e.g., perturbation method, variables). ")
    # STORY-502: Model Ranking
    ranking_criteria: List[str] = Field(["rmse", "complexity", "aic"], description="List of criteria for ranking models (e.g., 'rmse', 'complexity', 'aic', 'bic').")


class PdeDiscoveryResultResponse(BaseModel):
    id: int
    job_id: int
    owner_id: int
    discovery_algorithm: str
    target_variable: str
    candidate_features_path: str
    discovered_equation: Optional[str] = None
    canonical_equation: Optional[str] = Field(None, description="The canonicalized form of the discovered equation (STORY-503).")
    equation_metrics: Optional[Dict[str, Any]] = None # STORY-501: Will include RMSE, AIC/BIC
    uncertainty_metrics: Optional[Dict[str, Any]] = Field(None, description="Metrics quantifying uncertainty (e.g., confidence intervals for coefficients) (STORY-405).")
    sensitivity_analysis_results_path: Optional[str] = Field(None, description="Path to sensitivity analysis results in object storage (STORY-504).")
    model_ranking_score: Optional[float] = Field(None, description="Overall score for model ranking (STORY-502).")
    results_path: Optional[str] = None
    logs_path: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
