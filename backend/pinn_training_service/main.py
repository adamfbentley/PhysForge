from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional
import logging
from datetime import datetime
import uuid

from .config import settings
from .schemas import PinnTrainingRequest, PinnTrainingResponse, TrainingStatus
from .pinn_config import PinnTrainingConfig, NetworkArchitecture, TrainingParameters, PhysicsLossConfig
from .pinn_model import build_model
from .pinn_solver import PinnSolver
from .worker_task import train_pinn_worker
from .storage_utils import save_model_checkpoint, load_model_checkpoint
from .pinn_results import PinnTrainingResult

import torch
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory job tracking (in production, use Redis or database)
training_jobs: Dict[str, Dict[str, Any]] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("PINN Training Service starting up...")
    logger.info(f"PyTorch version: {torch.__version__}")
    logger.info(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        logger.info(f"CUDA device: {torch.cuda.get_device_name(0)}")
    yield
    logger.info("PINN Training Service shutting down.")

app = FastAPI(
    title="PINN Training Service",
    description="Trains Physics-Informed Neural Networks (PINNs) on spatiotemporal data.",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/", tags=["Root"])
async def read_root():
    return {
        "message": "PINN Training Service is running!",
        "cuda_available": torch.cuda.is_available(),
        "pytorch_version": torch.__version__
    }

@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": "pinn_training_service",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/train", response_model=PinnTrainingResponse, tags=["Training"])
async def submit_training_job(
    request: PinnTrainingRequest,
    background_tasks: BackgroundTasks
) -> PinnTrainingResponse:
    """
    Submit a PINN training job.
    
    The training will be executed asynchronously as a background task.
    Use the returned job_id to check training status.
    """
    try:
        job_id = str(uuid.uuid4())
        
        # Initialize job tracking
        training_jobs[job_id] = {
            "status": "queued",
            "created_at": datetime.utcnow().isoformat(),
            "progress": 0,
            "message": "Job queued for processing",
            "config": request.dict()
        }
        
        # Add background task
        background_tasks.add_task(
            execute_training_job,
            job_id=job_id,
            request=request
        )
        
        logger.info(f"PINN training job {job_id} submitted")
        
        return PinnTrainingResponse(
            job_id=job_id,
            status="queued",
            message="Training job submitted successfully"
        )
        
    except Exception as e:
        logger.error(f"Error submitting training job: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to submit training job: {str(e)}")

@app.get("/train/{job_id}/status", tags=["Training"])
async def get_training_status(job_id: str) -> Dict[str, Any]:
    """Get the current status of a training job."""
    if job_id not in training_jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    return training_jobs[job_id]

@app.get("/train/{job_id}/result", tags=["Training"])
async def get_training_result(job_id: str) -> Dict[str, Any]:
    """Get the final result of a completed training job."""
    if job_id not in training_jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    job = training_jobs[job_id]
    
    if job["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Job {job_id} is not completed. Current status: {job['status']}"
        )
    
    return job.get("result", {})

@app.delete("/train/{job_id}", tags=["Training"])
async def cancel_training_job(job_id: str) -> Dict[str, str]:
    """Cancel a running training job."""
    if job_id not in training_jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    job = training_jobs[job_id]
    
    if job["status"] in ["completed", "failed", "cancelled"]:
        return {"message": f"Job {job_id} is already {job['status']}"}
    
    training_jobs[job_id]["status"] = "cancelled"
    training_jobs[job_id]["message"] = "Job cancelled by user"
    
    logger.info(f"Training job {job_id} cancelled")
    
    return {"message": f"Job {job_id} cancelled successfully"}

@app.get("/models/{model_id}", tags=["Models"])
async def get_model(model_id: str) -> Dict[str, Any]:
    """Retrieve a trained model checkpoint."""
    try:
        checkpoint_data = load_model_checkpoint(model_id)
        return {
            "model_id": model_id,
            "metadata": checkpoint_data.get("metadata", {}),
            "available": True
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Model {model_id} not found: {str(e)}")

async def execute_training_job(job_id: str, request: PinnTrainingRequest):
    """
    Execute a PINN training job.
    This runs as a background task.
    """
    try:
        # Update status
        training_jobs[job_id]["status"] = "running"
        training_jobs[job_id]["message"] = "Initializing training..."
        training_jobs[job_id]["started_at"] = datetime.utcnow().isoformat()
        
        logger.info(f"Starting PINN training job {job_id}")
        
        # Parse configuration
        config = PinnTrainingConfig(**request.config)
        
        # Prepare data
        x_data = np.array(request.x_data)
        t_data = np.array(request.t_data)
        u_data = np.array(request.u_data)
        
        # Validate data shapes
        if not (x_data.shape[0] == t_data.shape[0] == u_data.shape[0]):
            raise ValueError("x_data, t_data, and u_data must have the same number of samples")
        
        # Combine inputs
        X_train = np.column_stack([x_data, t_data])
        y_train = u_data.reshape(-1, 1)
        
        # Convert to tensors
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        X_tensor = torch.tensor(X_train, dtype=torch.float32, device=device)
        y_tensor = torch.tensor(y_train, dtype=torch.float32, device=device)
        
        # Build model
        input_dim = X_train.shape[1]
        model = build_model(input_dim, config.network_architecture)
        
        # Create solver
        solver = PinnSolver(model, config, device=device)
        
        # Training loop with progress updates
        training_jobs[job_id]["message"] = f"Training on {device.upper()}..."
        
        epochs = config.training_parameters.epochs
        log_interval = max(1, epochs // 20)  # Log 20 times during training
        
        losses = []
        
        for epoch in range(epochs):
            # Training step
            loss = solver.train_step(X_tensor, y_tensor)
            losses.append(loss)
            
            # Update progress
            if epoch % log_interval == 0 or epoch == epochs - 1:
                progress = int((epoch + 1) / epochs * 100)
                training_jobs[job_id]["progress"] = progress
                training_jobs[job_id]["current_loss"] = float(loss)
                training_jobs[job_id]["epoch"] = epoch + 1
                logger.info(f"Job {job_id} - Epoch {epoch+1}/{epochs}, Loss: {loss:.6f}")
        
        # Save model
        model_id = f"pinn_model_{job_id}"
        checkpoint_data = {
            "model_state_dict": model.state_dict(),
            "config": config.dict(),
            "training_losses": losses,
            "metadata": {
                "job_id": job_id,
                "input_dim": input_dim,
                "output_dim": config.network_architecture.output_dim,
                "epochs": epochs,
                "final_loss": float(losses[-1]),
                "device": device
            }
        }
        save_model_checkpoint(model_id, checkpoint_data)
        
        # Create result
        result = PinnTrainingResult(
            model_id=model_id,
            final_loss=float(losses[-1]),
            epochs=epochs,
            training_losses=losses,
            device=device,
            metadata=checkpoint_data["metadata"]
        )
        
        # Update job status
        training_jobs[job_id]["status"] = "completed"
        training_jobs[job_id]["message"] = "Training completed successfully"
        training_jobs[job_id]["progress"] = 100
        training_jobs[job_id]["completed_at"] = datetime.utcnow().isoformat()
        training_jobs[job_id]["result"] = result.dict()
        
        logger.info(f"PINN training job {job_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Training job {job_id} failed: {str(e)}")
        training_jobs[job_id]["status"] = "failed"
        training_jobs[job_id]["message"] = f"Training failed: {str(e)}"
        training_jobs[job_id]["error"] = str(e)
        training_jobs[job_id]["failed_at"] = datetime.utcnow().isoformat()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
