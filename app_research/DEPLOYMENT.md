# PhysForge Research Edition - Deployment Guide

This guide walks through deploying the research edition with PySR symbolic regression capabilities.

## ⚠️ Important: Starter Instance Required

**The research edition requires a paid Starter instance ($7/month)** due to PySR's memory and CPU requirements. The free tier has insufficient resources for symbolic regression.

## Quick Deploy to Render (Recommended)

### Prerequisites
- GitHub account
- Render account (sign up at [render.com](https://render.com))
- $7/month budget for Starter instance

### Steps

1. **Push code to GitHub** (if not already done):
```bash
cd PhysForge_-_Meta-Simulation
git add app_research/
git commit -m "Add research edition with PySR"
git push origin main
```

2. **Create new Web Service on Render**:
   - Go to [render.com/dashboard](https://dashboard.render.com)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select the `PhysForge_-_Meta-Simulation` repository

3. **Configure build settings**:
   - **Name**: `physforge-research`
   - **Region**: Oregon (best for research workloads)
   - **Branch**: `main`
   - **Root Directory**: `app_research`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt && python -c "import pysr; pysr.install()"`
   - **Start Command**: `uvicorn app:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: **Starter ($7/month)** ⚠️ Required for PySR

4. **Add environment variables**:
   - `KMP_DUPLICATE_LIB_OK` = `TRUE`
   - `PYTHON_VERSION` = `3.11.9`

5. **Deploy**:
   - Click "Create Web Service"
   - Wait 5-10 minutes for Julia + PySR installation
   - Your app will be live at `https://physforge-research-xxxx.onrender.com`

## Why Starter Instance?

### Free Tier Limitations (❌ Won't Work)
- **Cold starts**: App sleeps after 15 minutes of inactivity (takes ~30s to wake up)
- **Resources**: 512MB RAM, shared CPU (sufficient for testing/demos)
- **Build time**: Slower builds on free tier
- **Persistence**: SQLite database resets on redeploy (use PostgreSQL for production)

---

## Alternative: Deploy to Railway

Railway is another excellent option with similar free tier offerings.

### Steps

1. **Install Railway CLI**:
```bash
npm install -g @railway/cli
# or
curl -fsSL https://railway.app/install.sh | sh
```

2. **Login and deploy**:
```bash
cd app_simplified
railway login
railway init
railway up
```

3. **Set environment variable**:
```bash
railway variables set KMP_DUPLICATE_LIB_OK=TRUE
```

4. **Generate domain**:
```bash
railway domain
```

Your app will be live at the generated URL.

---

## Alternative: Docker Deployment

If you prefer containerized deployment (e.g., to AWS ECS, Google Cloud Run):

### Create Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Set environment
ENV KMP_DUPLICATE_LIB_OK=TRUE
ENV PORT=8000

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Build and run locally:
```bash
docker build -t physforge .
docker run -p 8000:8000 physforge
```

### Deploy to cloud:
- **Google Cloud Run**: `gcloud run deploy physforge --source .`
- **AWS ECS**: Push to ECR and create ECS task
- **Azure Container Instances**: `az container create`

---

## Post-Deployment

### Test your deployment:
```bash
curl https://your-app-url.onrender.com/health
```

Should return:
```json
{"status": "healthy", "service": "PhysForge Simplified"}
```

### Upload test data:
1. Navigate to your deployment URL
2. Upload `sample_heat_equation.csv`
3. Wait ~2 minutes for training
4. View discovered equation: `u_t = 0.010000·u_xx`

### Share your deployment:
Add to your GitHub profile README:
```markdown
🚀 **Live Demo**: [https://your-app-url.onrender.com](https://your-app-url.onrender.com)
```

---

## Troubleshooting

**App won't start:**
- Check logs in Render dashboard
- Verify `requirements.txt` includes all dependencies
- Ensure `PORT` environment variable is used correctly

**Slow cold starts:**
- Expected on free tier (app sleeps after 15 min)
- Consider keeping app warm with UptimeRobot (ping every 5 min)
- Or upgrade to paid tier ($7/month) for always-on

**Out of memory:**
- PyTorch is memory-intensive
- Reduce batch size or model size
- Consider using CPU-only PyTorch build
- Upgrade to 2GB RAM tier if needed

**Database resets:**
- SQLite doesn't persist on Render free tier
- Mount persistent volume (paid tier)
- Or switch to PostgreSQL (Render offers free 1GB database)

---

## Production Considerations

For serious production use beyond demos:

1. **Use PostgreSQL** instead of SQLite
2. **Add authentication** (currently open to all)
3. **Implement rate limiting** (prevent abuse)
4. **Add monitoring** (Sentry, Datadog)
5. **Use background workers** (Celery + Redis for long jobs)
6. **Cache results** (Redis for equation discovery)
7. **Scale horizontally** (multiple workers behind load balancer)

See the main PhysForge microservices architecture for production-ready design.
