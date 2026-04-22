# ⎈ K8s Banking App POC

A 3-tier banking application built to learn Kubernetes from scratch — progressing
from manual Pods all the way to ArgoCD GitOps.

## Stack
| Tier         | Technology          |
|-------------|---------------------|
| Database     | MySQL 8.0           |
| Backend      | Python Flask + JWT  |
| Frontend     | React 18 + Nginx    |
| Container    | Docker              |
| Orchestration| Kubernetes (K8s)    |
| CI/CD        | GitHub Actions      |
| GitOps       | ArgoCD              |
| Package Mgr  | Helm                |

## Project Structure
```
banking-app/
├── backend/            # Flask REST API
│   ├── app.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── tests/
├── frontend/           # React SPA
│   ├── src/
│   ├── Dockerfile
│   └── nginx.conf
├── database/
│   └── init.sql        # Schema + seed
├── k8s/
│   ├── 00-namespace.yaml
│   ├── 01-config-secret.yaml
│   ├── phase1-pods.yaml          # Phase 1: Manual Pods
│   ├── phase2-pv-pvc.yaml        # Phase 2: PV + PVC
│   ├── phase3-4-rs-deployment.yaml # Phase 3-4: RS + Deployment
│   └── phase5-statefulset.yaml   # Phase 5: StatefulSet
├── .github/
│   └── workflows/
│       ├── backend.yml
│       └── frontend.yml
└── docker-compose.yml
```

## Quick Start (Local Dev)
```bash
# Clone your repo
git clone https://github.com/YOUR_USERNAME/banking-app
cd banking-app

# Start all services
docker-compose up --build

# Access app
open http://localhost:3000
# Login: demo / demo1234
```

## K8s Learning Phases

### Phase 0 — Prerequisites
```bash
# Label your node (only need to do this once)
kubectl label node ip-10-0-3-126.ec2.internal role=banking-poc

# Create namespace
kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/01-config-secret.yaml
```

### Phase 1 — Manual Pods
```bash
# Replace GITHUB_USERNAME in the manifest first!
sed -i 's/GITHUB_USERNAME/your-username/g' k8s/phase1-pods.yaml

kubectl apply -f k8s/phase1-pods.yaml -n banking-poc
kubectl get pods -n banking-poc
kubectl logs pod/backend -n banking-poc

# Access frontend
# http://<node-ip>:30080
```

### Phase 2 — PV / PVC
```bash
kubectl apply -f k8s/phase2-pv-pvc.yaml
kubectl get pv,pvc -n banking-poc

# Test persistence: delete pod, data survives
kubectl delete pod mysql -n banking-poc
kubectl apply -f k8s/phase2-pv-pvc.yaml
```

### Phase 3 — ReplicaSet
```bash
kubectl apply -f k8s/phase3-4-rs-deployment.yaml

# Watch self-healing
kubectl delete pod -l app=backend -n banking-poc
kubectl get pods -n banking-poc -w
```

### Phase 4 — Deployment
```bash
# Rolling update
kubectl set image deployment/backend backend=ghcr.io/USER/banking-backend:v2 -n banking-poc
kubectl rollout status deployment/backend -n banking-poc

# Rollback
kubectl rollout undo deployment/backend -n banking-poc
kubectl rollout history deployment/backend -n banking-poc
```

### Phase 5 — StatefulSet
```bash
kubectl apply -f k8s/phase5-statefulset.yaml
kubectl get statefulset -n banking-poc
kubectl get pvc -n banking-poc   # each pod gets its own PVC
```

## CI/CD with GitHub Actions
1. Push to `main` → triggers test → build → push image to GHCR → update manifest
2. ArgoCD detects manifest change → auto-deploys to cluster

## Replacing placeholder
Before pushing to GitHub, replace `GITHUB_USERNAME` in all k8s manifests:
```bash
YOUR_GH_USER=your-github-username
find k8s/ -name "*.yaml" -exec sed -i "s/GITHUB_USERNAME/${YOUR_GH_USER}/g" {} \;
```

## API Reference
| Method | Endpoint                               | Auth | Description        |
|--------|----------------------------------------|------|--------------------|
| POST   | /api/auth/register                     | ✗    | Register user      |
| POST   | /api/auth/login                        | ✗    | Login              |
| GET    | /api/accounts                          | ✓    | List accounts      |
| POST   | /api/accounts                          | ✓    | Create account     |
| POST   | /api/accounts/:id/deposit              | ✓    | Deposit            |
| POST   | /api/accounts/:id/withdraw             | ✓    | Withdraw           |
| GET    | /api/accounts/:id/transactions         | ✓    | Transaction history|
| POST   | /api/transfer                          | ✓    | Transfer funds     |
| GET    | /health                                | ✗    | Health check       |
