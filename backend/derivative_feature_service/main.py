from fastapi import FastAPI, HTTPException, BackgroundTasks
from contextlib import asynccontextmanager
from typing import Dict, Any, List
import logging
from datetime import datetime
import uuid
import numpy as np
import torch

from .config import settings
from .schemas import DerivativeRequest, DerivativeResponse, FeatureRequest, FeatureResponse
from .derivative_calculator import DerivativeCalculator
from .feature_generator import FeatureGenerator
from .storage_utils import load_dataset, save_features

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory job tracking
derivative_jobs: Dict[str, Dict[str, Any]] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Derivative Feature Service starting up...")
    logger.info(f"PyTorch version: {torch.__version__}")
    yield
    logger.info("Derivative Feature Service shutting down.")

app = FastAPI(
    title="Derivative Feature Service",
    description="Computes derivatives and generates features from PINN models for PDE discovery.",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/", tags=["Root"])
async def read_root():
    return {
        "message": "Derivative Feature Service is running!",
        "pytorch_version": torch.__version__
    }

@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": "derivative_feature_service",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/derivatives/compute", response_model=DerivativeResponse, tags=["Derivatives"])
async def compute_derivatives(
    request: DerivativeRequest,
    background_tasks: BackgroundTasks
) -> DerivativeResponse:
    """
    Compute derivatives from a trained PINN model.
    
    This computes spatial and temporal derivatives using automatic differentiation.
    """
    try:
        job_id = str(uuid.uuid4())
        
        derivative_jobs[job_id] = {
            "status": "queued",
            "created_at": datetime.utcnow().isoformat(),
            "progress": 0,
            "message": "Derivative computation queued"
        }
        
        background_tasks.add_task(
            execute_derivative_computation,
            job_id=job_id,
            request=request
        )
        
        logger.info(f"Derivative computation job {job_id} submitted")
        
        return DerivativeResponse(
            job_id=job_id,
            status="queued",
            message="Derivative computation submitted successfully"
        )
        
    except Exception as e:
        logger.error(f"Error submitting derivative computation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to submit job: {str(e)}")

@app.post("/features/generate", response_model=FeatureResponse, tags=["Features"])
async def generate_features(
    request: FeatureRequest,
    background_tasks: BackgroundTasks
) -> FeatureResponse:
    """
    Generate feature matrix for PDE discovery.
    
    This creates candidate terms (u, u_x, u_t, u_xx, u*u_x, etc.) for sparse regression.
    """
    try:
        job_id = str(uuid.uuid4())
        
        derivative_jobs[job_id] = {
            "status": "queued",
            "created_at": datetime.utcnow().isoformat(),
            "progress": 0,
            "message": "Feature generation queued"
        }
        
        background_tasks.add_task(
            execute_feature_generation,
            job_id=job_id,
            request=request
        )
        
        logger.info(f"Feature generation job {job_id} submitted")
        
        return FeatureResponse(
            job_id=job_id,
            status="queued",
            message="Feature generation submitted successfully"
        )
        
    except Exception as e:
        logger.error(f"Error submitting feature generation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to submit job: {str(e)}")

@app.get("/jobs/{job_id}/status", tags=["Jobs"])
async def get_job_status(job_id: str) -> Dict[str, Any]:
    """Get the current status of a derivative/feature job."""
    if job_id not in derivative_jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    return derivative_jobs[job_id]

@app.get("/jobs/{job_id}/result", tags=["Jobs"])
async def get_job_result(job_id: str) -> Dict[str, Any]:
    """Get the final result of a completed job."""
    if job_id not in derivative_jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    job = derivative_jobs[job_id]
    
    if job["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Job {job_id} is not completed. Current status: {job['status']}"
        )
    
    return job.get("result", {})

async def execute_derivative_computation(job_id: str, request: DerivativeRequest):
    """Execute derivative computation job."""
    try:
        derivative_jobs[job_id]["status"] = "running"
        derivative_jobs[job_id]["message"] = "Computing derivatives..."
        derivative_jobs[job_id]["started_at"] = datetime.utcnow().isoformat()
        
        logger.info(f"Starting derivative computation job {job_id}")
        
        # Initialize calculator
        calculator = DerivativeCalculator(
            model_path=request.model_id,
            device='cuda' if torch.cuda.is_available() else 'cpu'
        )
        
        # Prepare data
        x_data = np.array(request.x_data)
        t_data = np.array(request.t_data)
        
        # Compute derivatives
        derivatives = calculator.compute_all_derivatives(
            x_data=x_data,
            t_data=t_data,
            derivative_orders=request.derivative_orders
        )
        
        # Save results
        result_id = f"derivatives_{job_id}"
        save_features(result_id, derivatives)
        
        # Update job status
        derivative_jobs[job_id]["status"] = "completed"
        derivative_jobs[job_id]["message"] = "Derivatives computed successfully"
        derivative_jobs[job_id]["progress"] = 100
        derivative_jobs[job_id]["completed_at"] = datetime.utcnow().isoformat()
        derivative_jobs[job_id]["result"] = {
            "result_id": result_id,
            "derivative_shapes": {k: v.shape for k, v in derivatives.items()},
            "available_derivatives": list(derivatives.keys())
        }
        
        logger.info(f"Derivative computation job {job_id} completed")
        
    except Exception as e:
        logger.error(f"Derivative computation job {job_id} failed: {str(e)}")
        derivative_jobs[job_id]["status"] = "failed"
        derivative_jobs[job_id]["message"] = f"Computation failed: {str(e)}"
        derivative_jobs[job_id]["error"] = str(e)
        derivative_jobs[job_id]["failed_at"] = datetime.utcnow().isoformat()

async def execute_feature_generation(job_id: str, request: FeatureRequest):
    """Execute feature generation job."""
    try:
        derivative_jobs[job_id]["status"] = "running"
        derivative_jobs[job_id]["message"] = "Generating features..."
        derivative_jobs[job_id]["started_at"] = datetime.utcnow().isoformat()
        
        logger.info(f"Starting feature generation job {job_id}")
        
        # Initialize generator
        generator = FeatureGenerator(
            polynomial_degree=request.polynomial_degree,
            include_cross_terms=request.include_cross_terms
        )
        
        # Load derivatives
        derivatives = load_dataset(request.derivative_result_id)
        
        # Generate features
        feature_matrix, feature_names = generator.generate_feature_library(derivatives)
        
        # Save results
        result_id = f"features_{job_id}"
        save_features(result_id, {
            "feature_matrix": feature_matrix,
            "feature_names": feature_names,
            "metadata": {
                "polynomial_degree": request.polynomial_degree,
                "include_cross_terms": request.include_cross_terms,
                "num_features": len(feature_names),
                "num_samples": feature_matrix.shape[0]
            }
        })
        
        # Update job status
        derivative_jobs[job_id]["status"] = "completed"
        derivative_jobs[job_id]["message"] = "Features generated successfully"
        derivative_jobs[job_id]["progress"] = 100
        derivative_jobs[job_id]["completed_at"] = datetime.utcnow().isoformat()
        derivative_jobs[job_id]["result"] = {
            "result_id": result_id,
            "feature_matrix_shape": feature_matrix.shape,
            "num_features": len(feature_names),
            "feature_names": feature_names
        }
        
        logger.info(f"Feature generation job {job_id} completed")
        
    except Exception as e:
        logger.error(f"Feature generation job {job_id} failed: {str(e)}")
        derivative_jobs[job_id]["status"] = "failed"
        derivative_jobs[job_id]["message"] = f"Generation failed: {str(e)}"
        derivative_jobs[job_id]["error"] = str(e)
        derivative_jobs[job_id]["failed_at"] = datetime.utcnow().isoformat()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
