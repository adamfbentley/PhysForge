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
COPY data_management_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY data_management_service/ .

# Expose port
EXPOSE 8002

# Run the service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]