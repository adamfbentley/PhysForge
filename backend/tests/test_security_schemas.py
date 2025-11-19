import pytest
from pydantic import ValidationError

# Import the schemas directly
from backend.derivative_feature_service.schemas import DerivativeJobConfig
from backend.pde_discovery_service.schemas import PDEDiscoveryConfig

# Mock data for required fields not related to output_name for DerivativeJobConfig
MOCK_DERIVATIVE_CONFIG_BASE = {
    "pinn_model_path": "s3://bucket/model.pt",
    "input_dim": 2,
    "output_dim": 1,
    "network_architecture": {"layers": [10, 10], "activation": "tanh"},
    "output_grid": {
        "independent_variables": ["x", "t"],
        "grid_resolution": {"x": 100, "t": 50},
        "domain_bounds": {"x": [0.0, 1.0], "t": [0.0, 1.0]}
    },
    "max_derivative_order": 2,
}

# Mock data for required fields not related to output_name for PDEDiscoveryConfig
MOCK_PDE_DISCOVERY_CONFIG_BASE = {
    "derivative_results_path": "s3://bucket/deriv_results.hdf5",
    "target_variable": "du_dt",
    "independent_variables": ["x", "t"],
    "dependent_variable": "u",
    "candidate_features": ["u", "du_dx", "du_dt"],
    "discovery_algorithm": "SINDy",
    "sindy_config": {"optimizer": "STLSQ", "threshold": 0.01},
}


# --- Tests for DerivativeJobConfig output_name ---
@pytest.mark.parametrize("valid_name", [
    "my_output",
    "output-123",
    "output_data.hdf5",
    "results.v1.0",
    "a",
    "long_name_with_underscores_and_numbers_123",
    "file.name.with.dots"
])
def test_derivative_job_config_output_name_valid(valid_name):
    config_data = {**MOCK_DERIVATIVE_CONFIG_BASE, "output_name": valid_name}
    config = DerivativeJobConfig(**config_data)
    assert config.output_name == valid_name

@pytest.mark.parametrize("invalid_name", [
    "../path_traversal",
    "path/traversal",
    "path\\traversal",
    " contains_space",
    "contains space ",
    "contains/slash",
    "contains\\backslash",
    ".starts_with_dot",
    "ends_with_dot.",
    "contains:colon",
    "contains*asterisk",
    "contains?question",
    "contains\"quote",
    "contains<lessthan",
    "contains>greaterthan",
    "contains|pipe",
    "contains`backtick",
    "contains'singlequote",
    "contains@at",
    "contains!exclamation",
    "contains#hash",
    "contains$dollar",
    "contains%percent",
    "contains^caret",
    "contains&ampersand",
    "contains(paren",
    "contains)paren",
    "contains+plus",
    "contains=equals",
    "contains{brace",
    "contains}brace",
    "contains[bracket",
    "contains]bracket",
    "contains~tilde",
    "contains,comma",
    "contains;semicolon",
    "contains'apostrophe",
    "contains\"doublequote",
    "contains`backtick",
    "contains\nnewline",
    "contains\ttab",
    "", # Empty string is not allowed by Field(..., pattern=...)
])
def test_derivative_job_config_output_name_invalid(invalid_name):
    config_data = {**MOCK_DERIVATIVE_CONFIG_BASE, "output_name": invalid_name}
    with pytest.raises(ValidationError) as exc_info:
        DerivativeJobConfig(**config_data)
    assert "output_name" in str(exc_info.value)
    assert "string does not match regex" in str(exc_info.value)

# --- Tests for PDEDiscoveryConfig output_name ---
@pytest.mark.parametrize("valid_name", [
    "pde_results",
    "equation-model-1",
    "discovery_output.json",
    "model.v2.0",
    "b",
    "another_long_name_with_numbers_and_dots_123.456",
    "final.equation.txt"
])
def test_pde_discovery_config_output_name_valid(valid_name):
    config_data = {**MOCK_PDE_DISCOVERY_CONFIG_BASE, "output_name": valid_name}
    config = PDEDiscoveryConfig(**config_data)
    assert config.output_name == valid_name

@pytest.mark.parametrize("invalid_name", [
    "../pde_output",
    "pde/output",
    "pde\\output",
    " starts_with_space",
    "ends_with_space ",
    "contains/slash",
    "contains\\backslash",
    ".starts_with_dot",
    "ends_with_dot.",
    "contains:colon",
    "contains*asterisk",
    "contains?question",
    "contains\"quote",
    "contains<lessthan",
    "contains>greaterthan",
    "contains|pipe",
    "contains`backtick",
    "contains'singlequote",
    "contains@at",
    "contains!exclamation",
    "contains#hash",
    "contains$dollar",
    "contains%percent",
    "contains^caret",
    "contains&ampersand",
    "contains(paren",
    "contains)paren",
    "contains+plus",
    "contains=equals",
    "contains{brace",
    "contains}brace",
    "contains[bracket",
    "contains]bracket",
    "contains~tilde",
    "contains,comma",
    "contains;semicolon",
    "contains'apostrophe",
    "contains\"doublequote",
    "contains`backtick",
    "contains\nnewline",
    "contains\ttab",
    "", # Empty string is not allowed by Field(..., pattern=...)
])
def test_pde_discovery_config_output_name_invalid(invalid_name):
    config_data = {**MOCK_PDE_DISCOVERY_CONFIG_BASE, "output_name": invalid_name}
    with pytest.raises(ValidationError) as exc_info:
        PDEDiscoveryConfig(**config_data)
    assert "output_name" in str(exc_info.value)
    assert "string does not match regex" in str(exc_info.value)
