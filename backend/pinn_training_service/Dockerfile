FROM python:3.11-slim

# Install system dependencies for scientific computing
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    libopenblas-dev \
    liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements-worker.txt .
RUN pip install --no-cache-dir -r requirements-worker.txt

# Copy all backend services (workers need access to all modules)
COPY . .

# Run the RQ worker
CMD ["python", "job_orchestration_service/worker.py"]