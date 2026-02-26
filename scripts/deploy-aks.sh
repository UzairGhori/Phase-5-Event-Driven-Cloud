#!/usr/bin/env bash
# =============================================================================
# deploy-aks.sh — AKS Provisioning & Deployment Script
# Task: T-E007 — GROUP E Cloud Deployment
#
# Provisions an AKS cluster and deploys the full todo-app stack including
# Dapr, NGINX Ingress, cert-manager, and all microservices.
#
# Prerequisites:
#   - Azure CLI (az) installed and logged in
#   - kubectl installed
#   - Dapr CLI installed
#   - Helm installed
#   - Container images pushed to ghcr.io/todo-app/*
#
# Usage:
#   bash scripts/deploy-aks.sh
#   RESOURCE_GROUP=mygroup CLUSTER_NAME=mycluster bash scripts/deploy-aks.sh
# =============================================================================
set -euo pipefail

# ---------------------------------------------------------------------------
# Configurable Variables (override via environment)
# ---------------------------------------------------------------------------
RESOURCE_GROUP="${RESOURCE_GROUP:-todo-app-rg}"
CLUSTER_NAME="${CLUSTER_NAME:-todo-app-aks}"
LOCATION="${LOCATION:-eastus}"
NODE_COUNT="${NODE_COUNT:-3}"
VM_SIZE="${VM_SIZE:-Standard_D2s_v3}"
K8S_VERSION="${K8S_VERSION:-1.30}"
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
  command -v az       >/dev/null 2>&1 || missing+=(az)
  command -v kubectl  >/dev/null 2>&1 || missing+=(kubectl)
  command -v dapr     >/dev/null 2>&1 || missing+=(dapr)
  command -v helm     >/dev/null 2>&1 || missing+=(helm)

  if [[ ${#missing[@]} -gt 0 ]]; then
    err "Missing required tools: ${missing[*]}"
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
    err "Missing required secrets: ${missing[*]}. Export them before running this script."
  fi
  log "All required secrets are set"
}

# ---------------------------------------------------------------------------
# Phase 1: Create Azure Resource Group
# ---------------------------------------------------------------------------
phase1_resource_group() {
  log "Phase 1 — Creating Azure resource group: $RESOURCE_GROUP in $LOCATION"
  az group create \
    --name "$RESOURCE_GROUP" \
    --location "$LOCATION" \
    --output none
  info "Resource group '$RESOURCE_GROUP' ready"
}

# ---------------------------------------------------------------------------
# Phase 2: Create AKS Cluster
# ---------------------------------------------------------------------------
phase2_create_aks() {
  log "Phase 2 — Creating AKS cluster: $CLUSTER_NAME ($VM_SIZE x $NODE_COUNT)"
  az aks create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$CLUSTER_NAME" \
    --location "$LOCATION" \
    --node-count "$NODE_COUNT" \
    --node-vm-size "$VM_SIZE" \
    --kubernetes-version "$K8S_VERSION" \
    --enable-managed-identity \
    --enable-addons monitoring \
    --network-plugin azure \
    --network-policy azure \
    --generate-ssh-keys \
    --output none
  info "AKS cluster '$CLUSTER_NAME' provisioned"
}

# ---------------------------------------------------------------------------
# Phase 3: Get AKS Credentials
# ---------------------------------------------------------------------------
phase3_get_credentials() {
  log "Phase 3 — Getting AKS credentials"
  az aks get-credentials \
    --resource-group "$RESOURCE_GROUP" \
    --name "$CLUSTER_NAME" \
    --overwrite-existing
  info "kubectl context set to '$CLUSTER_NAME'"
  kubectl cluster-info
}

# ---------------------------------------------------------------------------
# Phase 4: Install Dapr on AKS
# ---------------------------------------------------------------------------
phase4_install_dapr() {
  log "Phase 4 — Installing Dapr runtime v$DAPR_RUNTIME_VERSION"
  if dapr status -k 2>/dev/null | grep -q "Running"; then
    info "Dapr already installed on cluster, skipping"
  else
    dapr init -k --runtime-version "$DAPR_RUNTIME_VERSION" --wait
    info "Dapr installed and running"
  fi
}

# ---------------------------------------------------------------------------
# Phase 5: Install NGINX Ingress Controller + cert-manager
# ---------------------------------------------------------------------------
phase5_install_ingress_certmanager() {
  log "Phase 5a — Installing NGINX Ingress Controller"
  helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx 2>/dev/null || true
  helm repo update
  if helm status ingress-nginx -n ingress-nginx >/dev/null 2>&1; then
    info "NGINX Ingress Controller already installed, skipping"
  else
    helm install ingress-nginx ingress-nginx/ingress-nginx \
      --create-namespace \
      --namespace ingress-nginx \
      --set controller.replicaCount=2 \
      --set controller.service.externalTrafficPolicy=Local \
      --wait
    info "NGINX Ingress Controller installed"
  fi

  log "Phase 5b — Installing cert-manager"
  helm repo add jetstack https://charts.jetstack.io 2>/dev/null || true
  helm repo update
  if helm status cert-manager -n cert-manager >/dev/null 2>&1; then
    info "cert-manager already installed, skipping"
  else
    helm install cert-manager jetstack/cert-manager \
      --create-namespace \
      --namespace cert-manager \
      --set crds.enabled=true \
      --wait
    info "cert-manager installed"
  fi
}

# ---------------------------------------------------------------------------
# Phase 6: Create Namespaces + Secrets
# ---------------------------------------------------------------------------
phase6_namespaces_secrets() {
  log "Phase 6a — Creating namespaces"
  kubectl apply -f "$PROJECT_ROOT/k8s/production/namespaces/"
  info "Namespaces created"

  log "Phase 6b — Creating Kubernetes secrets"

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
    --from-literal=username="$REDPANDA_USERNAME" \
    --from-literal=password="$REDPANDA_PASSWORD" \
    --dry-run=client -o yaml | kubectl apply -f -

  info "All secrets created in todo-app namespace"
}

# ---------------------------------------------------------------------------
# Phase 7: Apply Production Manifests
# ---------------------------------------------------------------------------
phase7_apply_manifests() {
  log "Phase 7 — Applying production manifests via kustomize"

  # Update image tags if IMAGE_TAG is set
  if [[ "$IMAGE_TAG" != "latest" ]]; then
    info "Setting image tags to $IMAGE_TAG"
    cd "$PROJECT_ROOT/k8s/production"
    kubectl kustomize . | \
      sed "s|IMAGE_TAG|${IMAGE_TAG}|g" | \
      kubectl apply -f -
    cd "$PROJECT_ROOT"
  else
    kubectl apply -k "$PROJECT_ROOT/k8s/production/"
  fi

  info "All production manifests applied"
}

# ---------------------------------------------------------------------------
# Phase 8: Wait for Rollout & Verify
# ---------------------------------------------------------------------------
phase8_verify() {
  log "Phase 8 — Waiting for deployments to roll out"

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
      --timeout=120s || {
        echo "WARNING: $svc rollout did not complete within 120s"
      }
  done

  log "Pod status:"
  kubectl get pods -n todo-app -o wide

  log "Service status:"
  kubectl get svc -n todo-app

  log "Ingress status:"
  kubectl get ingress -n todo-app

  log "Dapr sidecar status:"
  dapr status -k

  # Get external IP
  local external_ip
  external_ip=$(kubectl get svc -n ingress-nginx ingress-nginx-controller \
    -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending")

  echo ""
  echo "============================================="
  echo "  AKS Deployment Complete"
  echo "============================================="
  echo "  Resource Group:  $RESOURCE_GROUP"
  echo "  Cluster Name:    $CLUSTER_NAME"
  echo "  Location:        $LOCATION"
  echo "  Nodes:           $NODE_COUNT x $VM_SIZE"
  echo "  External IP:     $external_ip"
  echo "  Dapr Version:    $DAPR_RUNTIME_VERSION"
  echo "  Image Tag:       $IMAGE_TAG"
  echo "============================================="
  echo ""
  echo "Next steps:"
  echo "  1. Point your DNS to $external_ip"
  echo "  2. Verify TLS certificate: kubectl get certificate -n todo-app"
  echo "  3. Access the app: https://<your-domain>"
  echo ""
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
  log "Starting AKS deployment for todo-app"
  echo ""

  check_prerequisites
  validate_secrets

  phase1_resource_group
  phase2_create_aks
  phase3_get_credentials
  phase4_install_dapr
  phase5_install_ingress_certmanager
  phase6_namespaces_secrets
  phase7_apply_manifests
  phase8_verify

  log "AKS deployment completed successfully"
}

main "$@"
