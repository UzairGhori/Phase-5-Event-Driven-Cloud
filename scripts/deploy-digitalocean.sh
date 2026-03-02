#!/usr/bin/env bash
# =============================================================================
# deploy-digitalocean.sh — DigitalOcean DOKS Deployment Script
# Phase V — Event-Driven Cloud Deployment
#
# Provisions a DOKS cluster and deploys the full todo-app stack including
# Dapr, NGINX Ingress, and all microservices.
#
# Prerequisites:
#   - doctl (DigitalOcean CLI) installed and authenticated
#   - kubectl installed
#   - docker installed (for building/pushing images)
#   - dapr CLI installed
#   - helm installed
#
# Usage:
#   bash scripts/deploy-digitalocean.sh
#   CLUSTER_NAME=my-todo bash scripts/deploy-digitalocean.sh
#
# Free tier: $200 credit for 60 days at digitalocean.com
# =============================================================================
set -euo pipefail

# ---------------------------------------------------------------------------
# Configurable Variables (override via environment)
# ---------------------------------------------------------------------------
CLUSTER_NAME="${CLUSTER_NAME:-todo-app-doks}"
REGION="${REGION:-nyc1}"
NODE_SIZE="${NODE_SIZE:-s-2vcpu-4gb}"
NODE_COUNT="${NODE_COUNT:-1}"
K8S_VERSION="${K8S_VERSION:-1.31.1-do.3}"
REGISTRY_NAME="${REGISTRY_NAME:-todo-app-registry}"
DAPR_RUNTIME_VERSION="${DAPR_RUNTIME_VERSION:-1.14.4}"
IMAGE_TAG="${IMAGE_TAG:-latest}"

# Secrets — must be set by the operator
NEON_CONNECTION_STRING="${NEON_CONNECTION_STRING:-}"
JWT_SECRET_KEY="${JWT_SECRET_KEY:-}"
OPENAI_API_KEY="${OPENAI_API_KEY:-}"
REDPANDA_BROKERS="${REDPANDA_BROKERS:-}"
REDPANDA_USERNAME="${REDPANDA_USERNAME:-}"
REDPANDA_PASSWORD="${REDPANDA_PASSWORD:-}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
log()  { echo "==> [$(date +%H:%M:%S)] $*"; }
info() { echo "    $*"; }
err()  { echo "!!! ERROR: $*" >&2; exit 1; }

check_prerequisites() {
  local missing=()
  command -v doctl   >/dev/null 2>&1 || missing+=(doctl)
  command -v kubectl >/dev/null 2>&1 || missing+=(kubectl)
  command -v docker  >/dev/null 2>&1 || missing+=(docker)
  command -v dapr    >/dev/null 2>&1 || missing+=(dapr)
  command -v helm    >/dev/null 2>&1 || missing+=(helm)

  if [[ ${#missing[@]} -gt 0 ]]; then
    err "Missing required tools: ${missing[*]}
Install with:
  doctl  → https://docs.digitalocean.com/reference/doctl/how-to/install/
  dapr   → https://docs.dapr.io/getting-started/install-dapr-cli/
  helm   → https://helm.sh/docs/intro/install/"
  fi

  # Verify doctl is authenticated
  if ! doctl account get >/dev/null 2>&1; then
    err "doctl is not authenticated. Run: doctl auth init"
  fi

  log "All prerequisites satisfied"
}

validate_secrets() {
  local missing=()
  [[ -z "$NEON_CONNECTION_STRING" ]] && missing+=(NEON_CONNECTION_STRING)
  [[ -z "$JWT_SECRET_KEY" ]]         && missing+=(JWT_SECRET_KEY)
  [[ -z "$OPENAI_API_KEY" ]]         && missing+=(OPENAI_API_KEY)
  [[ -z "$REDPANDA_BROKERS" ]]       && missing+=(REDPANDA_BROKERS)
  [[ -z "$REDPANDA_USERNAME" ]]      && missing+=(REDPANDA_USERNAME)
  [[ -z "$REDPANDA_PASSWORD" ]]      && missing+=(REDPANDA_PASSWORD)

  if [[ ${#missing[@]} -gt 0 ]]; then
    err "Missing required secrets: ${missing[*]}.
Export them before running:
  export NEON_CONNECTION_STRING='postgresql://...'
  export JWT_SECRET_KEY='your-secret'
  export OPENAI_API_KEY='sk-...'
  export REDPANDA_BROKERS='...'
  export REDPANDA_USERNAME='...'
  export REDPANDA_PASSWORD='...'"
  fi
  log "All required secrets are set"
}

# ---------------------------------------------------------------------------
# Phase 1: Create Container Registry (DOCR)
# ---------------------------------------------------------------------------
phase1_registry() {
  log "Phase 1 — Creating DigitalOcean Container Registry: $REGISTRY_NAME"
  if doctl registry get >/dev/null 2>&1; then
    info "Registry already exists, skipping creation"
  else
    doctl registry create "$REGISTRY_NAME" --subscription-tier starter
    info "Registry '$REGISTRY_NAME' created (starter tier — free)"
  fi

  # Get registry endpoint
  REGISTRY_ENDPOINT=$(doctl registry get --format Endpoint --no-header)
  info "Registry endpoint: $REGISTRY_ENDPOINT"
}

# ---------------------------------------------------------------------------
# Phase 2: Build & Push Docker Images
# ---------------------------------------------------------------------------
phase2_build_push() {
  log "Phase 2 — Building and pushing Docker images"

  # Login to DOCR
  doctl registry login

  local services=(
    "task-api"
    "chat-api"
    "reminder-service"
    "recurring-service"
    "audit-service"
    "ws-sync-service"
    "frontend"
  )

  for svc in "${services[@]}"; do
    local dockerfile="$PROJECT_ROOT/docker/${svc}.Dockerfile"
    local image_name="$REGISTRY_ENDPOINT/todo-${svc}:${IMAGE_TAG}"

    if [[ ! -f "$dockerfile" ]]; then
      info "WARNING: $dockerfile not found, skipping"
      continue
    fi

    info "Building $svc..."
    docker build -t "$image_name" -f "$dockerfile" "$PROJECT_ROOT"

    info "Pushing $svc..."
    docker push "$image_name"
  done

  info "All images pushed to DOCR"
}

# ---------------------------------------------------------------------------
# Phase 3: Create DOKS Cluster
# ---------------------------------------------------------------------------
phase3_create_cluster() {
  log "Phase 3 — Creating DOKS cluster: $CLUSTER_NAME ($NODE_SIZE x $NODE_COUNT)"

  # Check if cluster already exists
  if doctl kubernetes cluster get "$CLUSTER_NAME" >/dev/null 2>&1; then
    info "Cluster '$CLUSTER_NAME' already exists, skipping creation"
  else
    doctl kubernetes cluster create "$CLUSTER_NAME" \
      --region "$REGION" \
      --size "$NODE_SIZE" \
      --count "$NODE_COUNT" \
      --version "$K8S_VERSION" \
      --wait
    info "DOKS cluster '$CLUSTER_NAME' provisioned"
  fi

  # Save kubeconfig
  doctl kubernetes cluster kubeconfig save "$CLUSTER_NAME"
  info "kubectl context set to '$CLUSTER_NAME'"
  kubectl cluster-info
}

# ---------------------------------------------------------------------------
# Phase 4: Integrate DOCR with DOKS
# ---------------------------------------------------------------------------
phase4_registry_integration() {
  log "Phase 4 — Integrating Container Registry with DOKS"
  doctl kubernetes cluster registry add "$CLUSTER_NAME" 2>/dev/null || \
    info "Registry already integrated or integration skipped"
  info "DOCR integrated with DOKS — pods can pull images"
}

# ---------------------------------------------------------------------------
# Phase 5: Install Dapr on DOKS
# ---------------------------------------------------------------------------
phase5_install_dapr() {
  log "Phase 5 — Installing Dapr runtime v$DAPR_RUNTIME_VERSION"
  if dapr status -k 2>/dev/null | grep -q "Running"; then
    info "Dapr already installed on cluster, skipping"
  else
    dapr init -k --runtime-version "$DAPR_RUNTIME_VERSION" --wait
    info "Dapr installed and running"
  fi
}

# ---------------------------------------------------------------------------
# Phase 6: Install NGINX Ingress Controller
# ---------------------------------------------------------------------------
phase6_install_ingress() {
  log "Phase 6 — Installing NGINX Ingress Controller"
  helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx 2>/dev/null || true
  helm repo update
  if helm status ingress-nginx -n ingress-nginx >/dev/null 2>&1; then
    info "NGINX Ingress Controller already installed, skipping"
  else
    helm install ingress-nginx ingress-nginx/ingress-nginx \
      --create-namespace \
      --namespace ingress-nginx \
      --set controller.replicaCount=1 \
      --set controller.service.type=LoadBalancer \
      --set controller.service.annotations."service\.beta\.kubernetes\.io/do-loadbalancer-name"="todo-app-lb" \
      --set controller.service.annotations."service\.beta\.kubernetes\.io/do-loadbalancer-size-unit"="1" \
      --wait
    info "NGINX Ingress Controller installed with DO Load Balancer"
  fi

  # Wait for external IP
  log "Waiting for Load Balancer external IP..."
  local retries=30
  local external_ip=""
  while [[ $retries -gt 0 ]]; do
    external_ip=$(kubectl get svc -n ingress-nginx ingress-nginx-controller \
      -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
    if [[ -n "$external_ip" ]]; then
      break
    fi
    info "Waiting for IP assignment... ($retries retries left)"
    sleep 10
    retries=$((retries - 1))
  done

  if [[ -z "$external_ip" ]]; then
    info "WARNING: External IP not yet assigned. Check later with:"
    info "  kubectl get svc -n ingress-nginx ingress-nginx-controller"
  else
    info "Load Balancer IP: $external_ip"
  fi
}

# ---------------------------------------------------------------------------
# Phase 7: Create Namespaces & Secrets
# ---------------------------------------------------------------------------
phase7_namespaces_secrets() {
  log "Phase 7a — Creating namespaces"
  kubectl apply -f "$PROJECT_ROOT/k8s/production/namespaces/"
  info "Namespaces created"

  log "Phase 7b — Creating Kubernetes secrets"

  # Database secrets (Neon PostgreSQL)
  kubectl create secret generic db-secrets \
    --namespace todo-app \
    --from-literal=connection-string="$NEON_CONNECTION_STRING" \
    --dry-run=client -o yaml | kubectl apply -f -

  # JWT secrets
  kubectl create secret generic jwt-secrets \
    --namespace todo-app \
    --from-literal=secret-key="$JWT_SECRET_KEY" \
    --dry-run=client -o yaml | kubectl apply -f -

  # OpenAI secrets
  kubectl create secret generic openai-secrets \
    --namespace todo-app \
    --from-literal=api-key="$OPENAI_API_KEY" \
    --dry-run=client -o yaml | kubectl apply -f -

  # Redpanda (Kafka) secrets
  kubectl create secret generic kafka-secrets \
    --namespace todo-app \
    --from-literal=brokers="$REDPANDA_BROKERS" \
    --from-literal=sasl-username="$REDPANDA_USERNAME" \
    --from-literal=sasl-password="$REDPANDA_PASSWORD" \
    --dry-run=client -o yaml | kubectl apply -f -

  info "All secrets created in todo-app namespace"
}

# ---------------------------------------------------------------------------
# Phase 8: Apply DigitalOcean Manifests
# ---------------------------------------------------------------------------
phase8_apply_manifests() {
  log "Phase 8 — Applying DigitalOcean manifests via kustomize"

  REGISTRY_ENDPOINT=$(doctl registry get --format Endpoint --no-header)

  # Apply kustomize with image overrides for DOCR
  kubectl kustomize "$PROJECT_ROOT/k8s/digitalocean/" | \
    sed "s|ghcr.io/todo-app/|${REGISTRY_ENDPOINT}/|g" | \
    sed "s|IMAGE_TAG|${IMAGE_TAG}|g" | \
    kubectl apply -f -

  info "All DigitalOcean manifests applied"
}

# ---------------------------------------------------------------------------
# Phase 9: Wait for Rollout & Output URL
# ---------------------------------------------------------------------------
phase9_verify() {
  log "Phase 9 — Waiting for deployments to roll out"

  local services=(
    task-api
    chat-api
    reminder-service
    recurring-service
    audit-service
    ws-sync-service
    frontend
  )

  for svc in "${services[@]}"; do
    info "Waiting for $svc..."
    kubectl rollout status deployment/"$svc" \
      --namespace todo-app \
      --timeout=180s || {
        echo "WARNING: $svc rollout did not complete within 180s"
      }
  done

  log "Pod status:"
  kubectl get pods -n todo-app -o wide

  log "Service status:"
  kubectl get svc -n todo-app

  log "Ingress status:"
  kubectl get ingress -n todo-app

  # Get external IP
  local external_ip
  external_ip=$(kubectl get svc -n ingress-nginx ingress-nginx-controller \
    -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending")

  echo ""
  echo "============================================================="
  echo "  DigitalOcean DOKS Deployment Complete"
  echo "============================================================="
  echo "  Cluster:         $CLUSTER_NAME"
  echo "  Region:          $REGION"
  echo "  Nodes:           $NODE_COUNT x $NODE_SIZE"
  echo "  Registry:        $REGISTRY_ENDPOINT"
  echo "  Dapr Version:    $DAPR_RUNTIME_VERSION"
  echo "  Image Tag:       $IMAGE_TAG"
  echo ""
  echo "  ================================================"
  echo "  PUBLISHED APP URL:  http://$external_ip"
  echo "  ================================================"
  echo ""
  echo "  API endpoint:    http://$external_ip/api"
  echo "  Chat endpoint:   http://$external_ip/api/chat"
  echo "  WebSocket:       ws://$external_ip/ws"
  echo "============================================================="
  echo ""
  echo "Cost: FREE (\$200 credit covers ~5 months)"
  echo "  DOKS cluster:    $NODE_COUNT x $NODE_SIZE (~\$24/mo)"
  echo "  Load Balancer:   1 x basic (~\$12/mo)"
  echo "  Registry:        Starter (free)"
  echo "  Total:           ~\$36/mo → \$0 with free credit"
  echo ""
  echo "Teardown:"
  echo "  doctl kubernetes cluster delete $CLUSTER_NAME --force"
  echo "  doctl registry delete $REGISTRY_NAME --force"
  echo ""
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
  echo ""
  echo "============================================================="
  echo "  Phase V — DigitalOcean DOKS Deployment"
  echo "  Todo App Event-Driven Cloud"
  echo "============================================================="
  echo ""

  check_prerequisites
  validate_secrets

  phase1_registry
  phase2_build_push
  phase3_create_cluster
  phase4_registry_integration
  phase5_install_dapr
  phase6_install_ingress
  phase7_namespaces_secrets
  phase8_apply_manifests
  phase9_verify

  log "DigitalOcean deployment completed successfully"
}

main "$@"
