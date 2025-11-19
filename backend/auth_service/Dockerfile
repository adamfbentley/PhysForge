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
COPY auth_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY auth_service/ .

# Expose port
EXPOSE 8001

# Run the service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]