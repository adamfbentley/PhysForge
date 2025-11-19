import json
import io
import logging
from typing import Dict, Any, List, Optional
import nbformat
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell
import httpx
import h5py
import numpy as np
import torch
from datetime import datetime

from .storage_utils import load_data_from_minio_path

logger = logging.getLogger(__name__)

class ReportGenerator:
    def __init__(self, dms_token: str):
        self.dms_token = dms_token

    async def _fetch_job_details_from_jos(self, job_id: int, jos_url: str) -> Dict[str, Any]:
        """Fetches full job details from the Job Orchestration Service."""
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {self.dms_token}"}
            response = await client.get(f"{jos_url}/jobs/{job_id}", headers=headers)
            response.raise_for_status()
            return response.json()

    async def generate_json_report(self, job_id: int, job_details: Dict[str, Any], jos_url: str) -> Dict[str, Any]:
        """
        Generates a comprehensive JSON discovery report (STORY-703).
        For this sprint, the JSON report primarily relies on paths and summary data from JOS.
        Future sprints may integrate more detailed data/metadata from other services (e.g., DMS).
        """
        logger.info(f"Generating JSON report for job {job_id}.")

        report_data = {
            "report_id": f"report-{job_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "job_id": job_id,
            "owner_id": job_details.get("owner_id"),
            "report_type": "json_summary",
            "generated_at": datetime.now().isoformat(),
            "job_summary": {
                "job_type": job_details.get("job_type"),
                "status": job_details.get("status"),
                "created_at": job_details.get("created_at"),
                "completed_at": job_details.get("completed_at"),
                "error_message": job_details.get("error_message"),
            },
            "pinn_training_details": {},
            "derivative_computation_details": {},
            "pde_discovery_details": {},
            "raw_job_config": job_details.get("config"),
            "minio_paths": {
                "pinn_model": job_details.get("results_path") if job_details.get("job_type") == "pinn_training" else None,
                "derivative_results": job_details.get("results_path") if job_details.get("job_type") == "derivative_computation" else None,
                "feature_library": job_details.get("feature_library_path"),
                "pde_discovery_results": job_details.get("results_path") if job_details.get("job_type") == "pde_discovery" else None,
                "sensitivity_analysis_results": job_details.get("sensitivity_analysis_results_path"),
                "job_logs": job_details.get("logs_path"),
            },
            "discovered_pde_summary": {
                "equation": job_details.get("discovered_equation"),
                "canonical_equation": job_details.get("canonical_equation"),
                "metrics": job_details.get("equation_metrics"),
                "uncertainty": job_details.get("uncertainty_metrics"),
                "ranking_score": job_details.get("model_ranking_score"),
            }
        }

        logger.info(f"JSON report for job {job_id} generated.")
        return report_data

    async def generate_jupyter_notebook(self, job_id: int, job_details: Dict[str, Any], jos_url: str) -> str:
        """Generates a reproducible Jupyter Notebook (STORY-704)."""
        logger.info(f"Generating Jupyter Notebook for job {job_id}.")

        nb = new_notebook()
        nb.cells.append(new_markdown_cell(f"# Scientific Discovery Report for Job ID: {job_id}"))
        nb.cells.append(new_markdown_cell(
            "This notebook provides a reproducible overview of the scientific discovery pipeline "
            f"for job `{job_id}`. It includes details on PINN training, derivative computation, "
            "and PDE discovery, along with code to load and visualize the results."
        ))

        # Add imports and configuration for the notebook environment
        nb.cells.append(new_code_cell(
            """import json
import h5py
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import torch
import os
import io
from minio import Minio
from minio.error import S3Error
import httpx

# --- Configuration (loaded from environment variables) ---
MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT', 'localhost:9000')
MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
MINIO_SECURE = os.getenv('MINIO_SECURE', 'False').lower() == 'true'

# User's JWT token for authenticating with other services (e.g., JOS, DMS)
# This token must be securely provided to the notebook environment (e.g., via an environment variable).
# Do NOT hardcode sensitive tokens.
USER_JWT_TOKEN = os.getenv('USER_JWT_TOKEN')

# Initialize MinIO client (uses static service credentials, not user JWT for MinIO auth)
def get_minio_client():
    try:
        client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=MINIO_SECURE
        )
        return client
    except S3Error as e:
        print(f"Error initializing MinIO client: {{e}}")
        return None

minio_client = get_minio_client()
if not minio_client:
    print("WARNING: MinIO client could not be initialized. Data loading from MinIO will fail.")

def load_minio_object(bucket_name: str, object_name: str):
    if not minio_client:
        raise RuntimeError("MinIO client not available.")
    try:
        response = minio_client.get_object(bucket_name, object_name)
        content = response.read()
        response.close()
        response.release_conn()
        print(f"Successfully loaded {{object_name}} from {{bucket_name}}.")
        return content
    except S3Error as e:
        print(f"Error loading {{object_name}} from {{bucket_name}}: {{e}}")
        raise

async def fetch_data_from_service(url: str, token: str):
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {{token}}"}
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

print("Setup complete. MinIO client initialized. USER_JWT_TOKEN is available if set.")
"""
        ))

        # Add job details as a JSON object
        nb.cells.append(new_markdown_cell("## Job Details from Job Orchestration Service"))
        nb.cells.append(new_code_cell(f"job_details = {json.dumps(job_details, indent=2)}\nprint(json.dumps(job_details, indent=2))"))

        # Example: Load PDE discovery results if available
        pde_discovery_results_path = job_details.get("minio_paths", {}).get("pde_discovery_results")
        if pde_discovery_results_path:
            nb.cells.append(new_markdown_cell("## PDE Discovery Results"))
            nb.cells.append(new_code_cell(
                f"""
pde_results_path = "{pde_discovery_results_path}"
if minio_client and pde_results_path:
    try:
        # Assuming path format is /bucket/object_name
        path_parts = pde_results_path.split('/', 2)
        bucket = path_parts[1]
        object_name = path_parts[2]
        pde_results_content = load_minio_object(bucket, object_name)
        pde_results = json.loads(pde_results_content.decode('utf-8'))
        print("Loaded PDE Discovery Results:")
        print(json.dumps(pde_results, indent=2))
        # Further visualization/analysis can go here
    except Exception as e:
        print(f"Failed to load PDE discovery results: {{e}}")
else:
    print("PDE discovery results path not available or MinIO client not initialized.")
"""
            ))
        
        # Add a placeholder for PINN model loading and evaluation
        pinn_model_path = job_details.get("minio_paths", {}).get("pinn_model")
        if pinn_model_path:
            nb.cells.append(new_markdown_cell("## PINN Model (Placeholder for Loading and Evaluation)"))
            nb.cells.append(new_code_cell(
                f"""
pinn_model_path = "{pinn_model_path}"
if minio_client and pinn_model_path:
    try:
        # Assuming path format is /bucket/object_name
        path_parts = pinn_model_path.split('/', 2)
        bucket = path_parts[1]
        object_name = path_parts[2]
        pinn_model_content = load_minio_object(bucket, object_name)
        # Example: If it's a PyTorch model, you might load it like this:
        # model = torch.load(io.BytesIO(pinn_model_content))
        print(f"PINN model content loaded from {{pinn_model_path}}. Further deserialization and evaluation needed.")
    except Exception as e:
        print(f"Failed to load PINN model: {{e}}")
else:
    print("PINN model path not available or MinIO client not initialized.")
"""
            ))

        # Add a placeholder for derivative computation results
        derivative_results_path = job_details.get("minio_paths", {}).get("derivative_results")
        if derivative_results_path:
            nb.cells.append(new_markdown_cell("## Derivative Computation Results (Placeholder)"))
            nb.cells.append(new_code_cell(
                f"""
derivative_results_path = "{derivative_results_path}"
if minio_client and derivative_results_path:
    try:
        # Assuming path format is /bucket/object_name
        path_parts = derivative_results_path.split('/', 2)
        bucket = path_parts[1]
        object_name = path_parts[2]
        derivative_results_content = load_minio_object(bucket, object_name)
        # Example: If it's an HDF5 file
        # with h5py.File(io.BytesIO(derivative_results_content), 'r') as f:
        #     data = {{key: f[key][()] for key in f.keys()}}
        print(f"Derivative results content loaded from {{derivative_results_path}}. Further deserialization and analysis needed.")
    except Exception as e:
        print(f"Failed to load derivative results: {{e}}")
else:
    print("Derivative results path not available or MinIO client not initialized.")
"""
            ))

        # Final markdown cell
        nb.cells.append(new_markdown_cell("## Conclusion"))
        nb.cells.append(new_markdown_cell(
            "This notebook serves as a starting point for exploring the results of your scientific discovery job. "
            "You can extend it with more detailed analysis, visualizations, and comparisons."
        ))

        logger.info(f"Jupyter Notebook for job {job_id} generated.")
        return nbformat.writes(nb)
