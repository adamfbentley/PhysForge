# Monitoring Stack Configuration

## Overview
This directory contains monitoring and observability configurations for the PhysForge platform using Prometheus, Grafana, and supporting tools.

## Architecture
```
Services -> Prometheus (metrics collection)
    ├── Node Exporter (system metrics)
    ├── cAdvisor (container metrics)
    ├── Application metrics (FastAPI, RQ, etc.)
    └── Blackbox Exporter (external checks)

Prometheus -> Grafana (visualization)
    ├── System dashboards
    ├── Application dashboards
    ├── Alerting rules
    └── Custom panels
```

## Files
- `docker-compose.monitoring.yml` - Monitoring stack services
- `prometheus.yml` - Prometheus configuration
- `grafana/provisioning/` - Grafana dashboards and datasources
- `alertmanager.yml` - Alert configuration
- `prometheus/rules.yml` - Alerting rules

## Metrics Collected
- **System**: CPU, memory, disk, network
- **Containers**: Resource usage, health status
- **Applications**: API response times, error rates, job queue status
- **Business**: Job completion rates, user activity, storage usage