from pydantic import BaseModel, Field, EmailStr, root_validator
from typing import List, Optional, Dict, Any, Literal, Union
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

# --- Active Experiment Service Schemas (STORY-601, STORY-602, STORY-603, STORY-604) ---

class ParameterSpaceDefinition(BaseModel):
    continuous_params: Dict[str, List[float]] = Field({}, description="Dictionary of continuous parameters with [min, max] bounds, e.g., {'x': [0.0, 1.0], 't': [0.0, 1.0]}.")
    categorical_params: Dict[str, List[Any]] = Field({}, description="Dictionary of categorical parameters with a list of allowed values, e.g., {'material': ['steel', 'aluminum']}.")

class LHSConfig(BaseModel):
    num_samples: int = Field(100, ge=1, description="Number of samples to generate using Latin Hypercube Sampling (STORY-602).")
    parameter_space: ParameterSpaceDefinition = Field(..., description="Definition of the parameter space to sample from (STORY-601).")

class BayesianOptimizationConfig(BaseModel):
    pde_discovery_job_id: int = Field(..., description="ID of the PDE Discovery job whose results (equation, uncertainty) will inform the optimization.")
    num_iterations: int = Field(10, ge=1, description="Number of Bayesian Optimization iterations to perform.")
    num_initial_samples: int = Field(10, ge=1, description="Number of initial samples to generate before starting optimization.")
    initial_design_method: Literal["LHS", "Random"] = Field("LHS", description="Method for generating initial samples.")
    acquisition_function: Literal["EI", "UCB"] = Field("EI", description="Acquisition function to use (Expected Improvement, Upper Confidence Bound).")
    parameter_space: ParameterSpaceDefinition = Field(..., description="Definition of the parameter space to optimize within (STORY-601).")
    target_metric_key: str = Field("rmse", description="Key of the metric from PDE discovery results to optimize (e.g., 'rmse', 'uncertainty_reduction'). Lower is better.")

class ActiveExperimentConfig(BaseModel):
    experiment_design_method: Literal["LHS", "BayesianOptimization"] = Field(..., description="Method to use for active experiment design (STORY-602, STORY-603).")
    lhs_config: Optional[LHSConfig] = Field(None, description="Configuration for Latin Hypercube Sampling.")
    bayesian_optimization_config: Optional[BayesianOptimizationConfig] = Field(None, description="Configuration for Bayesian Optimization.")
    output_name: str = Field(..., description="A name for the output active experiment results.")

    @root_validator(pre=True)
    def check_config_consistency(cls, values):
        method = values.get('experiment_design_method')
        lhs_config = values.get('lhs_config')
        bo_config = values.get('bayesian_optimization_config')

        if method == "LHS" and not lhs_config:
            raise ValueError("lhs_config must be provided if experiment_design_method is 'LHS'.")
        if method == "BayesianOptimization" and not bo_config:
            raise ValueError("bayesian_optimization_config must be provided if experiment_design_method is 'BayesianOptimization'.")
        if method == "LHS" and bo_config:
            raise ValueError("bayesian_optimization_config should not be provided if experiment_design_method is 'LHS'.")
        if method == "BayesianOptimization" and lhs_config:
            raise ValueError("lhs_config should not be provided if experiment_design_method is 'BayesianOptimization'.")
        return values

class OptimizationHistoryEntry(BaseModel):
    iteration: int = Field(..., description="Iteration number of the optimization.")
    proposed_point: Dict[str, Any] = Field(..., description="The parameters proposed in this iteration.")
    observed_metric: Optional[float] = Field(None, description="The observed metric value for the proposed point (from external simulation/experiment).")
    model_uncertainty: Optional[float] = Field(None, description="The model's estimated uncertainty at the proposed point.")
    expected_improvement: Optional[float] = Field(None, description="The expected improvement of the proposed point.")

class ActiveExperimentResultResponse(BaseModel):
    id: int
    job_id: int
    owner_id: int
    pde_discovery_result_path: Optional[str] = None
    experiment_design_method: str
    initial_parameters: Optional[Dict[str, Any]] = None
    proposed_parameters_path: Optional[str] = None
    optimization_history_path: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
