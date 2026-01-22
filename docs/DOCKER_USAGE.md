# Docker Usage Guide

## Quick Start

### Build the Image

```bash
# Build the Docker image
docker build -t apt:latest .

# Or use docker-compose
docker-compose build
```

### Run Tests

```bash
# Run smoke tests
docker run --rm -v $(pwd)/tests:/app/tests \
  -v $(pwd)/performance_results:/app/performance_results \
  apt:latest \
  pytest tests/definitions/ --perf-tags=smoke -v

# Run specific test file
docker run --rm -v $(pwd)/tests:/app/tests \
  -v $(pwd)/performance_results:/app/performance_results \
  apt:latest \
  pytest tests/definitions/unified_performance_test.yml -v

# Run with docker-compose
docker-compose run --rm apt \
  pytest tests/definitions/ --perf-tags=smoke -v
```

---

## Complete Stack with Monitoring

### Start Everything

```bash
# Start framework + Prometheus + Grafana
docker-compose up -d

# View logs
docker-compose logs -f apt

# Run tests
docker-compose exec apt \
  pytest tests/definitions/unified_performance_test.yml -v

# View results
open performance_results/unified_test/unified_performance_report.html
```

### Access Services

- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Test App**: http://localhost:8080

---

## Sharing the Framework

### Option 1: Share Docker Image

```bash
# Save image to file
docker save apt:latest | gzip > apt.tar.gz

# On another machine: Load image
gunzip -c apt.tar.gz | docker load

# Run tests
docker run --rm -v $(pwd)/tests:/app/tests apt:latest \
  pytest tests/definitions/ --perf-tags=smoke -v
```

### Option 2: Push to Registry

```bash
# Tag image
docker tag apt:latest your-registry.com/apt:latest

# Push to registry
docker push your-registry.com/apt:latest

# On another machine: Pull and run
docker pull your-registry.com/apt:latest
docker run --rm -v $(pwd)/tests:/app/tests \
  your-registry.com/apt:latest \
  pytest tests/definitions/ --perf-tags=smoke -v
```

### Option 3: Share docker-compose.yml

```bash
# Share these files:
# - docker-compose.yml
# - Dockerfile
# - requirements.txt
# - tests/
# - config/

# On another machine:
docker-compose up -d
docker-compose exec apt pytest tests/definitions/ -v
```

---

## Hyperscale Deployment

### Kubernetes Deployment

```yaml
# k8s-deployment.yml
apiVersion: batch/v1
kind: Job
metadata:
  name: apt
spec:
  template:
    spec:
      containers:
      - name: perf-test
        image: apt:latest
        command: ["pytest", "tests/definitions/", "--perf-tags=load", "-v"]
        volumeMounts:
        - name: test-results
          mountPath: /app/performance_results
      volumes:
      - name: test-results
        persistentVolumeClaim:
          claimName: perf-results-pvc
      restartPolicy: Never
```

```bash
# Deploy to Kubernetes
kubectl apply -f k8s-deployment.yml

# View logs
kubectl logs -f job/apt

# Get results
kubectl cp apt:/app/performance_results ./results
```

### AWS ECS/Fargate

```bash
# Push to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

docker tag apt:latest \
  <account-id>.dkr.ecr.us-east-1.amazonaws.com/apt:latest

docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/apt:latest

# Create ECS task definition and run
```

### Google Cloud Run

```bash
# Push to Google Container Registry
docker tag apt:latest gcr.io/<project-id>/apt:latest
docker push gcr.io/<project-id>/apt:latest

# Deploy to Cloud Run
gcloud run deploy apt \
  --image gcr.io/<project-id>/apt:latest \
  --platform managed \
  --region us-central1
```

---

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/perf-tests.yml
name: Performance Tests

on:
  schedule:
    - cron: '0 0 * * *'  # Daily
  workflow_dispatch:

jobs:
  perf-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build Docker image
        run: docker build -t apt:latest .
      
      - name: Run smoke tests
        run: |
          docker run --rm \
            -v ${{ github.workspace }}/tests:/app/tests \
            -v ${{ github.workspace }}/performance_results:/app/performance_results \
            apt:latest \
            pytest tests/definitions/ --perf-tags=smoke -v
      
      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: performance-results
          path: performance_results/
```

### GitLab CI

```yaml
# .gitlab-ci.yml
performance-tests:
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker build -t apt:latest .
    - docker run --rm -v $(pwd)/tests:/app/tests 
        -v $(pwd)/performance_results:/app/performance_results 
        apt:latest 
        pytest tests/definitions/ --perf-tags=smoke -v
  artifacts:
    paths:
      - performance_results/
    expire_in: 30 days
```

---

## Advanced Usage

### Custom Entrypoint

```bash
# Interactive shell
docker run -it --rm apt:latest /bin/bash

# Custom Python script
docker run --rm -v $(pwd)/tests:/app/tests \
  apt:latest \
  python tests/workflow/test_workflow_examples.py
```

### Environment Variables

```bash
# Pass environment variables
docker run --rm \
  -e AIRFLOW_TOKEN=your-token \
  -e DATABASE_URL=postgresql://... \
  -v $(pwd)/tests:/app/tests \
  apt:latest \
  pytest tests/definitions/workflow_performance_test.yml -v
```

### Network Access

```bash
# Access host services
docker run --rm --network host \
  -v $(pwd)/tests:/app/tests \
  apt:latest \
  pytest tests/definitions/ -v

# Custom network
docker network create perf-network
docker run --rm --network perf-network \
  -v $(pwd)/tests:/app/tests \
  apt:latest \
  pytest tests/definitions/ -v
```

---

## Image Details

### What's Included

- **Python 3.11** with all dependencies
- **Playwright** with Chromium browser
- **k6** latest version
- **JMeter 5.6.3**
- **All framework code** pre-installed
- **Java 11** (for JMeter)

### Image Size

- **Compressed**: ~800MB
- **Uncompressed**: ~2.5GB

### Optimization

```dockerfile
# Multi-stage build for smaller image (optional)
FROM apt:latest as builder
# ... build steps ...

FROM python:3.11-slim
COPY --from=builder /app /app
# ... minimal runtime ...
```

---

## Troubleshooting

### Issue: Playwright browser not found

```bash
# Rebuild with browser installation
docker build --no-cache -t apt:latest .
```

### Issue: Permission denied

```bash
# Run with user permissions
docker run --rm --user $(id -u):$(id -g) \
  -v $(pwd)/tests:/app/tests \
  apt:latest \
  pytest tests/definitions/ -v
```

### Issue: Out of memory

```bash
# Increase Docker memory
docker run --rm --memory=4g \
  -v $(pwd)/tests:/app/tests \
  apt:latest \
  pytest tests/definitions/ -v
```

---

## Summary

**Benefits of Docker Approach:**

✅ **Portable** - Run anywhere Docker runs
✅ **Consistent** - Same environment everywhere
✅ **Complete** - All tools bundled (Playwright, k6, JMeter)
✅ **Shareable** - Easy to distribute
✅ **Scalable** - Deploy to Kubernetes, ECS, Cloud Run
✅ **CI/CD Ready** - Works in any pipeline

**One command to rule them all:**
```bash
docker run --rm -v $(pwd)/tests:/app/tests apt:latest \
  pytest tests/definitions/ --perf-tags=smoke -v
```

🚀 **The framework is now truly portable and hyperscale-ready!**
