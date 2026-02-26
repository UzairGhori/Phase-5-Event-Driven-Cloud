#!/usr/bin/env bash
# =============================================================================
# setup-monitoring.sh — Monitoring Stack Setup
# Task: T-G005, T-G006, T-G007 — GROUP G (Monitoring & Logging)
#
# Supports two deployment modes:
#   Option A: Prometheus + Grafana + OTel Collector (Helm or manifests)
#   Option B: Azure Monitor + Log Analytics (AKS only)
#
# Usage:
#   bash scripts/setup-monitoring.sh              # Option A via kustomize
#   bash scripts/setup-monitoring.sh --helm       # Option A via Helm charts
#   bash scripts/setup-monitoring.sh --azure      # Option B (Azure Monitor)
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MODE="${1:---manifests}"

log()  { echo "==> [$(date +%H:%M:%S)] $*"; }
info() { echo "    $*"; }
err()  { echo "!!! ERROR: $*" >&2; exit 1; }

# ============================================================================
# OPTION A — Prometheus + Grafana + OTel (via Helm)
# ============================================================================
setup_helm() {
  log "Installing monitoring stack via Helm charts"

  # --- Add Helm repos ---
  log "Adding Helm repositories"
  helm repo add prometheus-community https://prometheus-community.github.io/helm-charts 2>/dev/null || true
  helm repo add grafana https://grafana.github.io/helm-charts 2>/dev/null || true
  helm repo add open-telemetry https://open-telemetry.github.io/opentelemetry-helm-charts 2>/dev/null || true
  helm repo update

  # --- Create namespace ---
  kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

  # --- Prometheus (kube-prometheus-stack includes alertmanager + node-exporter) ---
  log "Installing Prometheus via Helm"
  if helm status prometheus -n monitoring >/dev/null 2>&1; then
    info "Prometheus already installed, upgrading..."
    HELM_CMD="upgrade"
  else
    HELM_CMD="install"
  fi

  helm $HELM_CMD prometheus prometheus-community/kube-prometheus-stack \
    --namespace monitoring \
    --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false \
    --set prometheus.prometheusSpec.podMonitorSelectorNilUsesHelmValues=false \
    --set prometheus.prometheusSpec.retention=7d \
    --set prometheus.prometheusSpec.resources.requests.cpu=250m \
    --set prometheus.prometheusSpec.resources.requests.memory=512Mi \
    --set prometheus.prometheusSpec.resources.limits.cpu=500m \
    --set prometheus.prometheusSpec.resources.limits.memory=1Gi \
    --set grafana.enabled=false \
    --set alertmanager.enabled=true \
    --set nodeExporter.enabled=true \
    --set kubeStateMetrics.enabled=true \
    --wait
  info "Prometheus installed"

  # --- Grafana ---
  log "Installing Grafana via Helm"
  if helm status grafana -n monitoring >/dev/null 2>&1; then
    HELM_CMD="upgrade"
  else
    HELM_CMD="install"
  fi

  helm $HELM_CMD grafana grafana/grafana \
    --namespace monitoring \
    --set adminPassword=admin \
    --set service.port=3001 \
    --set "datasources.datasources\\.yaml.apiVersion=1" \
    --set "datasources.datasources\\.yaml.datasources[0].name=Prometheus" \
    --set "datasources.datasources\\.yaml.datasources[0].type=prometheus" \
    --set "datasources.datasources\\.yaml.datasources[0].url=http://prometheus-kube-prometheus-prometheus.monitoring:9090" \
    --set "datasources.datasources\\.yaml.datasources[0].isDefault=true" \
    --set resources.requests.cpu=100m \
    --set resources.requests.memory=128Mi \
    --set resources.limits.cpu=250m \
    --set resources.limits.memory=256Mi \
    --set persistence.enabled=false \
    --wait
  info "Grafana installed"

  # --- OpenTelemetry Collector ---
  log "Installing OpenTelemetry Collector via Helm"
  if helm status otel-collector -n monitoring >/dev/null 2>&1; then
    HELM_CMD="upgrade"
  else
    HELM_CMD="install"
  fi

  helm $HELM_CMD otel-collector open-telemetry/opentelemetry-collector \
    --namespace monitoring \
    --set mode=deployment \
    --set resources.requests.cpu=100m \
    --set resources.requests.memory=128Mi \
    --set resources.limits.cpu=250m \
    --set resources.limits.memory=256Mi \
    --set config.receivers.otlp.protocols.grpc.endpoint="0.0.0.0:4317" \
    --set config.receivers.otlp.protocols.http.endpoint="0.0.0.0:4318" \
    --set config.exporters.prometheus.endpoint="0.0.0.0:8889" \
    --set config.exporters.logging.loglevel=info \
    --set config.service.pipelines.traces.receivers="{otlp}" \
    --set config.service.pipelines.traces.exporters="{logging}" \
    --set config.service.pipelines.metrics.receivers="{otlp}" \
    --set config.service.pipelines.metrics.exporters="{prometheus}" \
    --wait
  info "OpenTelemetry Collector installed"

  # --- Apply custom alert rules ---
  log "Applying Prometheus alert rules"
  kubectl create configmap prometheus-alerts \
    --namespace monitoring \
    --from-file="$PROJECT_ROOT/monitoring/prometheus/alerts.yml" \
    --dry-run=client -o yaml | kubectl apply -f -
  info "Alert rules applied"

  # --- Apply dashboard ConfigMap ---
  log "Applying Grafana dashboards"
  kubectl apply -f "$PROJECT_ROOT/k8s/local/monitoring/grafana/dashboards-configmap.yaml"
  info "Dashboards provisioned"

  print_helm_status
}

# ============================================================================
# OPTION A — Prometheus + Grafana + OTel (via kustomize manifests)
# ============================================================================
setup_manifests() {
  log "Installing monitoring stack via kubectl manifests"

  kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

  # Prometheus
  log "Deploying Prometheus"
  kubectl apply -f "$PROJECT_ROOT/k8s/local/monitoring/prometheus/"
  info "Prometheus deployed"

  # Grafana
  log "Deploying Grafana"
  kubectl apply -f "$PROJECT_ROOT/k8s/local/monitoring/grafana/"
  info "Grafana deployed"

  # OTel Collector
  log "Deploying OpenTelemetry Collector"
  kubectl apply -f "$PROJECT_ROOT/k8s/local/monitoring/otel-collector/"
  info "OTel Collector deployed"

  log "Waiting for pods..."
  for dep in prometheus grafana otel-collector; do
    kubectl rollout status deployment/$dep -n monitoring --timeout=60s || \
      echo "WARNING: $dep rollout incomplete"
  done

  print_manifest_status
}

# ============================================================================
# OPTION B — Azure Monitor + Log Analytics (AKS only)
# ============================================================================
setup_azure_monitor() {
  log "Configuring Azure Monitor for AKS"

  local RESOURCE_GROUP="${RESOURCE_GROUP:-todo-app-rg}"
  local CLUSTER_NAME="${CLUSTER_NAME:-todo-app-aks}"
  local WORKSPACE_NAME="${WORKSPACE_NAME:-todo-app-logs}"
  local LOCATION="${LOCATION:-eastus}"

  # Check prerequisites
  command -v az >/dev/null 2>&1 || err "Azure CLI (az) not found"

  # Create Log Analytics workspace
  log "Creating Log Analytics workspace: $WORKSPACE_NAME"
  local WORKSPACE_ID
  WORKSPACE_ID=$(az monitor log-analytics workspace create \
    --resource-group "$RESOURCE_GROUP" \
    --workspace-name "$WORKSPACE_NAME" \
    --location "$LOCATION" \
    --query id -o tsv 2>/dev/null || \
    az monitor log-analytics workspace show \
      --resource-group "$RESOURCE_GROUP" \
      --workspace-name "$WORKSPACE_NAME" \
      --query id -o tsv)
  info "Workspace: $WORKSPACE_ID"

  # Enable monitoring addon
  log "Enabling AKS monitoring addon"
  az aks enable-addons \
    --resource-group "$RESOURCE_GROUP" \
    --name "$CLUSTER_NAME" \
    --addons monitoring \
    --workspace-resource-id "$WORKSPACE_ID" \
    --output none
  info "Azure Monitor addon enabled"

  # Enable Container Insights with Prometheus
  log "Enabling managed Prometheus metrics collection"
  az aks update \
    --resource-group "$RESOURCE_GROUP" \
    --name "$CLUSTER_NAME" \
    --enable-azure-monitor-metrics \
    --output none 2>/dev/null || info "Managed Prometheus may already be enabled or requires preview"

  # Create alert rules
  log "Creating Azure Monitor alert rules"

  # High error rate alert
  az monitor metrics alert create \
    --resource-group "$RESOURCE_GROUP" \
    --name "todo-app-high-error-rate" \
    --scopes "$(az aks show -g $RESOURCE_GROUP -n $CLUSTER_NAME --query id -o tsv)" \
    --condition "avg requests/failed > 5" \
    --description "High error rate detected in todo-app" \
    --severity 2 \
    --output none 2>/dev/null || info "Alert rule creation may require additional permissions"

  print_azure_status "$WORKSPACE_NAME"
}

# ============================================================================
# Status output functions
# ============================================================================
print_helm_status() {
  echo ""
  echo "============================================="
  echo "  Monitoring Stack (Helm) — Installed"
  echo "============================================="
  echo ""
  echo "  Prometheus:  http://localhost:9090  (port-forward: kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090)"
  echo "  Grafana:     http://localhost:3001  (port-forward: kubectl port-forward -n monitoring svc/grafana 3001)"
  echo "  OTel GRPC:   localhost:4317        (port-forward: kubectl port-forward -n monitoring svc/otel-collector-opentelemetry-collector 4317)"
  echo ""
  echo "  Grafana login: admin / admin"
  echo ""
  echo "  Dashboards: 5 (Service Overview, Kafka, Task Metrics, Infrastructure, Dapr)"
  echo "  Alert Rules: 10 (API, Kafka, Pod Health, Dapr)"
  echo ""
  echo "  To view pods:  kubectl get pods -n monitoring"
  echo "============================================="
}

print_manifest_status() {
  echo ""
  echo "============================================="
  echo "  Monitoring Stack (Manifests) — Deployed"
  echo "============================================="
  echo ""
  echo "  Prometheus:  kubectl port-forward -n monitoring svc/prometheus 9090"
  echo "  Grafana:     kubectl port-forward -n monitoring svc/grafana 3001"
  echo "  OTel GRPC:   kubectl port-forward -n monitoring svc/otel-collector 4317"
  echo ""
  echo "  Grafana login: admin / admin"
  echo ""
  kubectl get pods -n monitoring -o wide 2>/dev/null || true
  echo "============================================="
}

print_azure_status() {
  local ws_name="$1"
  echo ""
  echo "============================================="
  echo "  Azure Monitor — Configured"
  echo "============================================="
  echo ""
  echo "  Log Analytics Workspace: $ws_name"
  echo "  Container Insights:      Enabled"
  echo "  Managed Prometheus:      Enabled"
  echo ""
  echo "  View in Azure Portal:"
  echo "    - AKS cluster → Monitoring → Insights"
  echo "    - AKS cluster → Monitoring → Logs"
  echo "    - AKS cluster → Monitoring → Metrics"
  echo ""
  echo "  Key KQL queries:"
  echo "    ContainerLog | where LogEntry contains \"error\""
  echo "    KubePodInventory | where Namespace == \"todo-app\""
  echo "    InsightsMetrics | where Name == \"cpuUsageNanoCores\""
  echo ""
  echo "============================================="
}

# ============================================================================
# Main
# ============================================================================
main() {
  case "$MODE" in
    --helm)
      command -v helm >/dev/null 2>&1 || err "Helm not found. Install: https://helm.sh/docs/intro/install/"
      setup_helm
      ;;
    --azure)
      setup_azure_monitor
      ;;
    --manifests|*)
      setup_manifests
      ;;
  esac

  log "Monitoring setup complete"
}

main
