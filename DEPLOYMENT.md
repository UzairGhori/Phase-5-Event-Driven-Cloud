# Deployment Guide — Phase V

## Prerequisites

| Tool | Version | Required For |
|------|---------|-------------|
| Docker | 24+ | Building images |
| kubectl | 1.30+ | K8s management |
| Minikube | 1.33+ | Local deployment |
| Dapr CLI | 1.14+ | Dapr runtime |
| Helm | 3.14+ | Monitoring (optional) |
| Azure CLI | 2.60+ | AKS deployment |
| doctl | 1.100+ | DigitalOcean deployment |
| Node.js | 22 LTS | Frontend |
| Python | 3.12 | Backend services |

---

## Option 1: Local Deployment (Minikube)

### Automated Setup

```bash
bash scripts/setup-minikube.sh
```

This script:
1. Starts Minikube (8GB RAM, 4 CPUs)
2. Installs Dapr runtime
3. Installs Strimzi Kafka operator
4. Enables NGINX Ingress addon
5. Builds all 7 Docker images
6. Applies all manifests via kustomize
7. Waits for all pods to be Ready

### Manual Setup

```bash
# 1. Start Minikube
minikube start --memory=8192 --cpus=4 --driver=docker

# 2. Enable ingress
minikube addons enable ingress

# 3. Install Dapr
dapr init -k --wait

# 4. Install Strimzi operator
kubectl create namespace kafka
kubectl apply -f https://strimzi.io/install/latest?namespace=kafka

# 5. Build images (inside Minikube)
eval $(minikube docker-env)
docker build -f docker/task-api.Dockerfile -t todo-task-api:local .
docker build -f docker/chat-api.Dockerfile -t todo-chat-api:local .
docker build -f docker/reminder-service.Dockerfile -t todo-reminder-service:local .
docker build -f docker/recurring-service.Dockerfile -t todo-recurring-service:local .
docker build -f docker/audit-service.Dockerfile -t todo-audit-service:local .
docker build -f docker/ws-sync-service.Dockerfile -t todo-ws-sync-service:local .
docker build -f docker/frontend.Dockerfile -t todo-frontend:local .

# 6. Update secrets (edit with real values)
cp k8s/local/secrets/db-secrets.yaml k8s/local/secrets/db-secrets-actual.yaml
# Edit the base64 values in the copied file

# 7. Apply all manifests
kubectl apply -k k8s/local/

# 8. Wait for pods
kubectl wait --for=condition=Ready pods --all -n todo-app --timeout=300s
```

### Access

```bash
# Port forwarding
bash scripts/port-forward.sh

# Or manually:
kubectl port-forward -n todo-app svc/frontend 3000:3000 &
kubectl port-forward -n todo-app svc/task-api 8000:8000 &
kubectl port-forward -n monitoring svc/prometheus 9090:9090 &
kubectl port-forward -n monitoring svc/grafana 3001:3001 &
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Task API | http://localhost:8000/api |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3001 (admin/admin) |

### Teardown

```bash
bash scripts/teardown-minikube.sh
```

---

## Option 2: Production Deployment (AKS)

### Prerequisites

```bash
# Login to Azure
az login

# Verify subscription
az account show
```

### Required Secrets

Set these environment variables before deployment:

```bash
export NEON_CONNECTION_STRING="postgresql://user:pass@host/dbname?sslmode=require"
export JWT_SECRET_KEY="your-256-bit-secret-key"
export OPENAI_API_KEY="sk-..."
export REDPANDA_BROKERS="broker1.redpanda.com:9092"
export REDPANDA_USERNAME="your-username"
export REDPANDA_PASSWORD="your-password"
```

### Automated Deployment

```bash
# Default: eastus, 3 nodes, Standard_D2s_v3
bash scripts/deploy-aks.sh

# Custom configuration
RESOURCE_GROUP=my-rg \
CLUSTER_NAME=my-cluster \
LOCATION=westus2 \
NODE_COUNT=5 \
VM_SIZE=Standard_D4s_v3 \
bash scripts/deploy-aks.sh
```

### Script Phases

| Phase | Action | Duration |
|-------|--------|----------|
| 1 | Create Azure Resource Group | ~5s |
| 2 | Create AKS Cluster | ~5-8 min |
| 3 | Get AKS Credentials | ~5s |
| 4 | Install Dapr v1.14.4 | ~30s |
| 5 | Install NGINX Ingress + cert-manager | ~2 min |
| 6 | Create Namespaces + Secrets | ~10s |
| 7 | Apply Production Manifests | ~30s |
| 8 | Verify Rollout | ~2 min |

### Post-Deployment

```bash
# Get external IP
kubectl get svc -n ingress-nginx ingress-nginx-controller -o jsonpath='{.status.loadBalancer.ingress[0].ip}'

# Verify all pods
kubectl get pods -n todo-app

# Verify Dapr
dapr status -k

# Verify TLS certificate
kubectl get certificate -n todo-app

# Check HPA status
kubectl get hpa -n todo-app
```

### Resource Allocation (Production)

| Service | CPU Req/Limit | Memory Req/Limit | Replicas (HPA) |
|---------|--------------|------------------|-----------------|
| task-api | 250m/500m | 256Mi/512Mi | 2-5 |
| chat-api | 250m/500m | 256Mi/512Mi | 1-3 |
| frontend | 250m/500m | 256Mi/512Mi | 2-4 |
| ws-sync | 100m/250m | 128Mi/256Mi | 1-3 |
| reminder | 100m/250m | 128Mi/256Mi | 1 |
| recurring | 100m/250m | 128Mi/256Mi | 1 |
| audit | 100m/250m | 128Mi/256Mi | 1 |

---

## Option 3: DigitalOcean Deployment (DOKS)

### Prerequisites

```bash
# Install doctl
# https://docs.digitalocean.com/reference/doctl/how-to/install/

# Authenticate
doctl auth init

# Verify
doctl account get
```

### Required Secrets

```bash
export NEON_CONNECTION_STRING="postgresql://user:pass@host/dbname?sslmode=require"
export JWT_SECRET_KEY="your-256-bit-secret-key"
export OPENAI_API_KEY="sk-..."
export REDPANDA_BROKERS="broker1.redpanda.com:9092"
export REDPANDA_USERNAME="your-username"
export REDPANDA_PASSWORD="your-password"
```

### Automated Deployment

```bash
# Default: nyc1, 2 nodes, s-2vcpu-4gb
bash scripts/deploy-digitalocean.sh

# Custom configuration
CLUSTER_NAME=my-todo \
REGION=sfo3 \
NODE_COUNT=3 \
NODE_SIZE=s-4vcpu-8gb \
bash scripts/deploy-digitalocean.sh
```

### Script Phases

| Phase | Action | Duration |
|-------|--------|----------|
| 1 | Create Container Registry (DOCR) | ~10s |
| 2 | Build & Push Docker Images | ~5-10 min |
| 3 | Create DOKS Cluster | ~5-8 min |
| 4 | Integrate DOCR with DOKS | ~5s |
| 5 | Install Dapr v1.14.4 | ~30s |
| 6 | Install NGINX Ingress + DO LB | ~2 min |
| 7 | Create Namespaces + Secrets | ~10s |
| 8 | Apply DigitalOcean Manifests | ~30s |
| 9 | Verify Rollout & Output URL | ~2 min |

### Post-Deployment

```bash
# Get your Published App URL
kubectl get svc -n ingress-nginx ingress-nginx-controller \
  -o jsonpath='{.status.loadBalancer.ingress[0].ip}'

# Verify all pods
kubectl get pods -n todo-app

# Verify Dapr
dapr status -k
```

### Cost: FREE ($200 credit for 60 days)

| Resource | Monthly Cost | With Credit |
|----------|-------------|-------------|
| DOKS Cluster (1x s-2vcpu-4gb) | ~$24 | $0 |
| DO Load Balancer | ~$12 | $0 |
| Container Registry (Starter) | Free | $0 |
| **Total** | **~$36/month** | **$0 (covered by $200 credit)** |

### Teardown

```bash
doctl kubernetes cluster delete todo-app-doks --force
doctl registry delete todo-app-registry --force
```

---

## Option 4: GKE Deployment

### Prerequisites

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

### Cluster Creation

```bash
gcloud container clusters create todo-app-gke \
  --zone us-central1-a \
  --num-nodes 3 \
  --machine-type e2-standard-2 \
  --enable-network-policy \
  --release-channel regular

gcloud container clusters get-credentials todo-app-gke --zone us-central1-a
```

### Deploy

```bash
# Install Dapr
dapr init -k --runtime-version 1.14.4 --wait

# Install ingress + cert-manager (same as AKS)
helm install ingress-nginx ingress-nginx/ingress-nginx --create-namespace -n ingress-nginx
helm install cert-manager jetstack/cert-manager --create-namespace -n cert-manager --set crds.enabled=true

# Create secrets (same pattern as AKS Phase 6)
kubectl create namespace todo-app
kubectl create secret generic db-secrets -n todo-app --from-literal=connection-string="$NEON_CONNECTION_STRING"
kubectl create secret generic jwt-secrets -n todo-app --from-literal=secret-key="$JWT_SECRET_KEY"
kubectl create secret generic openai-secrets -n todo-app --from-literal=api-key="$OPENAI_API_KEY"
kubectl create secret generic kafka-secrets -n todo-app --from-literal=brokers="$REDPANDA_BROKERS" \
  --from-literal=username="$REDPANDA_USERNAME" --from-literal=password="$REDPANDA_PASSWORD"

# Apply manifests
kubectl apply -k k8s/production/
```

---

## Monitoring Setup

### Option A: Prometheus + Grafana (Helm)

```bash
bash scripts/setup-monitoring.sh --helm
```

Installs:
- **kube-prometheus-stack**: Prometheus + Alertmanager + node-exporter + kube-state-metrics
- **grafana**: With Prometheus datasource pre-configured
- **opentelemetry-collector**: OTLP receiver → Prometheus exporter + logging

### Option A: Prometheus + Grafana (Manifests)

```bash
bash scripts/setup-monitoring.sh --manifests
```

Applies K8s manifests from `k8s/local/monitoring/`.

### Option B: Azure Monitor

```bash
bash scripts/setup-monitoring.sh --azure
```

Configures:
- Log Analytics Workspace
- Container Insights addon
- Managed Prometheus metrics collection

### Alert Rules (10 total)

| Alert | Threshold | Severity |
|-------|-----------|----------|
| HighErrorRate | >5% 5xx in 5m | critical |
| HighP95Latency | >1s for 5m | warning |
| HighP99Latency | >3s for 5m | critical |
| KafkaConsumerLagHigh | >1000 for 5m | warning |
| KafkaPublishFailures | any for 2m | critical |
| PodRestartLoop | >3 in 15m | critical |
| PodNotReady | 5m | warning |
| HighCPUUsage | >80% limit | warning |
| HighMemoryUsage | >85% limit | warning |
| DaprSidecarUnhealthy | 2m | critical |

---

## CI/CD Pipeline

### GitHub Secrets Required

| Secret | Environment | Description |
|--------|-------------|-------------|
| `GITHUB_TOKEN` | (auto) | Container registry auth |
| `KUBE_CONFIG_STAGING` | staging | kubectl config for staging cluster |
| `KUBE_CONFIG_PRODUCTION` | production | kubectl config for production cluster |
| `GCP_SA_KEY_STAGING` | staging | GKE service account JSON (if GKE) |
| `GCP_SA_KEY_PRODUCTION` | production | GKE service account JSON (if GKE) |

### GitHub Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DEPLOY_TARGET` | `aks` | Deployment target: `aks`, `gke`, `minikube` |
| `GKE_CLUSTER_NAME` | — | GKE cluster name (if GKE) |
| `GKE_CLUSTER_LOCATION` | — | GKE cluster zone/region (if GKE) |

### GitHub Environments

Create two environments in repository settings:
- **staging**: Auto-deploy on push to main
- **production**: Requires manual approval

---

## Option 5: Oracle Cloud Free Tier (Docker on ARM VM)

**Cost: $0 forever** (Always Free Tier — no credit card charge)

This option runs all services as individual Docker containers on a single Oracle Cloud ARM A1 VM (4 OCPUs, 24GB RAM). No Kubernetes, no Kafka, no Dapr — just Docker with an Nginx reverse proxy.

### Prerequisites

| Tool | Required For |
|------|-------------|
| OCI Account | cloud.oracle.com (Always Free) |
| SSH Key Pair | VM access |
| rsync | File upload (pre-installed on most systems) |

### Step 1: Create the VM (OCI Console)

1. Sign in at [cloud.oracle.com](https://cloud.oracle.com)
2. Navigate to **Compute → Instances → Create Instance**
3. Configure:
   - **Name**: `todo-app`
   - **Image**: Ubuntu 22.04 (or Oracle Linux 9)
   - **Shape**: `VM.Standard.A1.Flex` — 4 OCPU, 24 GB RAM
   - **Boot Volume**: 50 GB (free tier allows up to 200 GB total)
   - **Networking**: Create new VCN or use existing, assign **public IP**
   - **SSH Key**: Upload your public key (`~/.ssh/id_rsa.pub`)
4. Click **Create**

### Step 2: Open Firewall Ports (OCI Security List)

1. Go to **Networking → Virtual Cloud Networks → your VCN**
2. Click the **Default Security List**
3. Add **Ingress Rules**:

| Source CIDR | Protocol | Dest Port | Description |
|-------------|----------|-----------|-------------|
| 0.0.0.0/0 | TCP | 80 | HTTP |
| 0.0.0.0/0 | TCP | 443 | HTTPS |

### Step 3: Deploy

```bash
# Automated deployment (builds + deploys everything)
bash scripts/deploy-oracle.sh <VM_PUBLIC_IP> [~/.ssh/your_key] [ubuntu]

# Example:
bash scripts/deploy-oracle.sh 129.153.42.100 ~/.ssh/oracle_key ubuntu
```

The script will:
1. Validate SSH connectivity
2. Install Docker on the VM
3. Upload project files via rsync
4. Generate production `.env` with random secrets
5. Build all 7 Docker images on the VM
6. Start 9 containers (postgres + 6 services + frontend + nginx)
7. Configure OS firewall
8. Run health checks

### Manual Deployment (if preferred)

```bash
# SSH into the VM
ssh -i ~/.ssh/oracle_key ubuntu@<PUBLIC_IP>

# Clone the project
git clone https://github.com/YOUR_USER/YOUR_REPO.git /opt/todo-app
cd /opt/todo-app

# Set environment variables
export POSTGRES_PASSWORD=$(openssl rand -hex 16)
export SECRET_KEY=$(openssl rand -hex 32)

# Make scripts executable and start
chmod +x scripts/oracle/*.sh
bash scripts/oracle/start-all.sh
```

### Managing Services

```bash
# Check status of all containers
bash scripts/oracle/status.sh

# Stop all services
bash scripts/oracle/stop-all.sh

# Restart a single service
bash scripts/oracle/run-task-api.sh

# View logs
docker logs todo-task-api
docker logs todo-frontend

# Full teardown (including data)
REMOVE_NETWORK=true REMOVE_VOLUMES=true bash scripts/oracle/stop-all.sh
```

### Access

| Service | URL |
|---------|-----|
| Frontend | http://\<PUBLIC_IP\> |
| Task API | http://\<PUBLIC_IP\>/api/health |
| Chat API | http://\<PUBLIC_IP\>/api/chat |

### Architecture (on the VM)

```
Internet → :80 Nginx
              ├── /           → frontend:3000
              ├── /api/*      → task-api:8000
              ├── /api/chat/* → chat-api:8001
              └── /ws         → ws-sync:8005 (WebSocket)

PostgreSQL :5432 ← task-api, audit-service
```

### Resource Usage (~2.5 GB RAM total)

| Container | RAM (approx) |
|-----------|-------------|
| PostgreSQL | ~200 MB |
| task-api | ~150 MB |
| chat-api | ~100 MB |
| reminder | ~100 MB |
| recurring | ~100 MB |
| audit | ~100 MB |
| ws-sync | ~100 MB |
| frontend | ~200 MB |
| nginx | ~10 MB |
| **Total** | **~1 GB** of 24 GB available |

### Teardown

```bash
# Stop services (keep data)
bash scripts/oracle/stop-all.sh

# Full cleanup (remove data volume)
REMOVE_VOLUMES=true REMOVE_NETWORK=true bash scripts/oracle/stop-all.sh

# Delete VM from OCI Console:
# Compute → Instances → todo-app → Terminate
```

---

## Option 6: Vercel + Neon (Serverless — Free)

**Cost: $0** — Vercel free tier + Neon free tier PostgreSQL.

This deploys the **backend** as a Vercel Python serverless function and the **frontend** as a standard Vercel Next.js app, with **Neon** providing a free PostgreSQL database.

### Step 1: Create Neon Database (Free)

1. Sign up at [neon.tech](https://neon.tech)
2. Create a new project → choose a region close to you
3. Copy the **connection string** — it looks like:
   ```
   postgresql://user:password@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```

### Step 2: Deploy Backend API (Vercel)

1. Go to [vercel.com](https://vercel.com) → Sign up / Log in with GitHub
2. Click **"Add New Project"** → Import your repository
3. Configure the project:
   - **Root Directory**: `.` (project root)
   - **Framework Preset**: Other
4. Add **Environment Variables**:

   | Variable | Value |
   |----------|-------|
   | `DATABASE_URL` | Your Neon connection string |
   | `SECRET_KEY` | A random string (`openssl rand -hex 32`) |
   | `CORS_ORIGINS` | `["*"]` (update with frontend URL later) |

5. Click **Deploy**
6. Copy the backend URL (e.g. `https://todo-api-xxx.vercel.app`)

### Step 3: Deploy Frontend (Vercel)

1. Click **"Add New Project"** again → Import the same repository
2. Configure:
   - **Root Directory**: `frontend`
   - **Framework Preset**: Next.js
3. Add **Environment Variables**:

   | Variable | Value |
   |----------|-------|
   | `BACKEND_URL` | Your backend Vercel URL (e.g. `https://todo-api-xxx.vercel.app`) |

4. Click **Deploy**
5. Your frontend is live at `https://todo-frontend-xxx.vercel.app`

### Step 4: Update CORS

Go back to the **backend project** settings on Vercel:
- Update `CORS_ORIGINS` to: `["https://todo-frontend-xxx.vercel.app"]`
- Redeploy

### Access

| Service | URL |
|---------|-----|
| Frontend | `https://todo-frontend-xxx.vercel.app` |
| Backend API | `https://todo-api-xxx.vercel.app/api/health` |
| Database | Neon dashboard at neon.tech |

### Limitations (Free Tier)

- Vercel Python functions: 10s timeout, 250MB bundle size
- Neon free: 0.5 GB storage, auto-suspend after 5 min inactivity
- No WebSocket support (ws-sync service not available)
- No Kafka/Dapr event processing (consumer services not deployed)
- Core CRUD (tasks, tags, auth) works fully

---

## Troubleshooting

### Pods Not Starting

```bash
# Check pod events
kubectl describe pod <pod-name> -n todo-app

# Check Dapr sidecar logs
kubectl logs <pod-name> -n todo-app -c daprd

# Check application logs
kubectl logs <pod-name> -n todo-app -c <service-name>
```

### Kafka Issues

```bash
# Check Strimzi Kafka status (local)
kubectl get kafka -n kafka

# Check Kafka topics
kubectl get kafkatopic -n kafka

# Check Dapr pub/sub
dapr components -k -n todo-app
```

### Database Issues

```bash
# Check PostgreSQL (local)
kubectl exec -it -n todo-app deploy/postgresql -- psql -U postgres -d todo_app

# Check Dapr state store
dapr components -k -n todo-app | grep statestore
```

### Docker Issues (Oracle Cloud / Docker deployment)

```bash
# Check all container status
bash scripts/oracle/status.sh

# View container logs
docker logs todo-task-api --tail 100
docker logs todo-frontend --tail 100

# Restart a specific service
bash scripts/oracle/run-task-api.sh

# Restart everything
bash scripts/oracle/stop-all.sh && bash scripts/oracle/start-all.sh

# Check if port 80 is accessible
curl http://localhost/nginx-health

# Connect to PostgreSQL
docker exec -it todo-postgres psql -U postgres -d todo_app
```

### Monitoring Issues

```bash
# Check Prometheus targets
kubectl port-forward -n monitoring svc/prometheus 9090 &
# Open http://localhost:9090/targets

# Check Grafana
kubectl port-forward -n monitoring svc/grafana 3001 &
# Open http://localhost:3001
```
