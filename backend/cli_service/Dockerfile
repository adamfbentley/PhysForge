FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY cli_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY cli_service/ .

# Default command for CLI
CMD ["python", "main.py"]