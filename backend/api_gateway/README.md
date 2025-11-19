# API Gateway Configuration (Traefik)

## Overview
This directory contains the API Gateway configuration using Traefik for routing, authentication, and load balancing across all microservices.

## Files
- `docker-compose.gateway.yml` - Gateway service definition
- `traefik.yml` - Main Traefik configuration
- `dynamic.yml` - Dynamic routing rules and middleware
- `middleware/` - Custom middleware configurations

## Architecture
```
Internet -> Traefik (API Gateway)
    ├── /auth/* -> auth_service:8000
    ├── /datasets/* -> data_management_service:8001
    ├── /jobs/* -> job_orchestration_service:8002
    ├── /reports/* -> reporting_service:8003
    ├── /active-experiments/* -> active_experiment_service:8004
    ├── /pde-discovery/* -> pde_discovery_service:8005
    ├── /pinn-training/* -> pinn_training_service:8006
    ├── /derivatives/* -> derivative_feature_service:8007
    └── / -> frontend:80 (React SPA)
```

## Features
- JWT authentication middleware
- Rate limiting per user
- CORS configuration
- Load balancing across service instances
- Health checks and service discovery
- SSL/TLS termination
- Request/response logging