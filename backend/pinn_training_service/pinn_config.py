from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal

class DatasetReference(BaseModel):
    dataset_id: int = Field(..., description="ID of the dataset from Data Management Service.")
    version_id: Optional[int] = Field(None, description="Specific version ID of the dataset. If None, use latest.")
    input_dataset_name: str = Field("x", description="Name of the dataset containing input features in the HDF5 file. (CQ-PTS-002)")
    output_dataset_name: str = Field("y", description="Name of the dataset containing output labels in the HDF5 file. (CQ-PTS-002)")

class NetworkArchitecture(BaseModel):
    network_type: Literal["MLP", "FourierFeatureMLP", "DeepONet"] = Field("MLP", description="Type of neural network architecture (e.g., 'MLP', 'FourierFeatureMLP', 'DeepONet').") # STORY-204
    layers: List[int] = Field(..., description="List of integers defining the number of neurons in each layer, e.g., [50, 50, 50].")
    activation: str = Field("tanh", description="Activation function for hidden layers (e.g., 'tanh', 'relu', 'sigmoid').")
    output_dim: int = Field(1, description="Output dimension of the neural network.")
    
    # Fourier Features specific
    fourier_features_scale: Optional[float] = Field(None, description="Scale for Fourier Features, if network_type is 'FourierFeatureMLP'.") # STORY-204

    # DeepONet specific
    branch_input_dim: Optional[int] = Field(None, description="Input dimension for the branch network in DeepONet. Required if network_type is 'DeepONet'.") # STORY-204
    trunk_input_dim: Optional[int] = Field(None, description="Input dimension for the trunk network in DeepONet. Required if network_type is 'DeepONet'.") # STORY-204
    branch_layers: Optional[List[int]] = Field(None, description="Layers for the branch network in DeepONet. Required if network_type is 'DeepONet'.") # STORY-204
    trunk_layers: Optional[List[int]] = Field(None, description="Layers for the trunk network in DeepONet. Required if network_type is 'DeepONet'.") # STORY-204

class TrainingParameters(BaseModel):
    optimizer: str = Field("Adam", description="Optimizer to use (e.g., 'Adam', 'LBFGS').")
    learning_rate: float = Field(1e-3, description="Initial learning rate.")
    epochs: int = Field(1000, description="Number of training epochs.")
    loss_weights: Dict[str, float] = Field({"data": 1.0, "pde": 1.0, "bc": 1.0, "ic": 1.0}, description="Weights for different components of the loss function.")
    batch_size: int = Field(64, description="Batch size for training.")
    
    # Custom loss/regularization (STORY-205)
    regularization_type: Optional[Literal["L1", "L2"]] = Field(None, description="Type of regularization (e.g., 'L1', 'L2').")
    regularization_weight: float = Field(0.0, description="Weight for the regularization term.")
    custom_loss_function_name: Optional[str] = Field(None, description="Name of a custom loss function to apply (e.g., 'weighted_mse', 'huber_loss').")
    custom_loss_params: Optional[Dict[str, Any]] = Field(None, description="Parameters for the custom loss function.")


class Condition(BaseModel):
    name: str = Field(..., description="Name of the condition (e.g., 'left_boundary', 'initial_time').")
    type: str = Field(..., description="Type of condition ('Dirichlet', 'Neumann', 'Robin', 'Initial').")
    variable: str = Field(..., description="The dependent variable the condition applies to (e.g., 'u').")
    location: Dict[str, Any] = Field(..., description="Spatial/temporal location of the condition (e.g., {'x': 0.0}, {'t': 0.0}).")
    value: Any = Field(..., description="The value of the condition (e.g., 0.0, 'sin(x)'). Can be a scalar or a string expression.")

class PhysicsLossConfig(BaseModel):
    pde_equation: str = Field(..., description="Symbolic representation of the PDE (e.g., 'du/dt + u*du/dx - (0.01/pi)*d2u/dx2 = 0').")
    independent_variables: List[str] = Field(..., description="List of independent variables in the PDE (e.g., ['x', 't']).")
    dependent_variables: List[str] = Field(..., description="List of dependent variables in the PDE (e.g., ['u']).")
    boundary_conditions: List[Condition] = Field([], description="List of boundary conditions.")
    initial_conditions: List[Condition] = Field([], description="List of initial conditions.")
    domain_bounds: Dict[str, List[float]] = Field(..., description="Dictionary of min/max bounds for each independent variable (e.g., {'x': [0.0, 1.0], 't': [0.0, 1.0]}).")
    num_domain_points: int = Field(10000, description="Number of collocation points for PDE loss.")
    num_boundary_points: int = Field(1000, description="Number of points for boundary conditions.")
    num_initial_points: int = Field(1000, description="Number of points for initial conditions.")

class PinnTrainingConfig(BaseModel):
    dataset_ref: Optional[DatasetReference] = Field(None, description="Reference to the dataset for data-driven loss.")
    network_architecture: NetworkArchitecture = Field(..., description="Configuration for the neural network architecture.")
    training_parameters: TrainingParameters = Field(..., description="Parameters for the training process.")
    physics_loss_config: Optional[PhysicsLossConfig] = Field(None, description="Configuration for physics-informed loss components.")
    output_name: str = Field(..., description="A name for the output model and results.")
