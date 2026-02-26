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

## Option 3: GKE Deployment

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

### Monitoring Issues

```bash
# Check Prometheus targets
kubectl port-forward -n monitoring svc/prometheus 9090 &
# Open http://localhost:9090/targets

# Check Grafana
kubectl port-forward -n monitoring svc/grafana 3001 &
# Open http://localhost:3001
```
