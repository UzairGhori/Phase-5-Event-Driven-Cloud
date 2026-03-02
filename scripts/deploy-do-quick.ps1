# =============================================================================
# deploy-do-quick.ps1 — Quick DigitalOcean DOKS Deployment (PowerShell)
# Phase V — Event-Driven Cloud Deployment
#
# Usage: Right-click -> Run with PowerShell, OR:
#   powershell -ExecutionPolicy Bypass -File scripts\deploy-do-quick.ps1
# =============================================================================

$ErrorActionPreference = "Stop"
$DOCTL = "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\DigitalOcean.Doctl_Microsoft.Winget.Source_8wekyb3d8bbwe\doctl.exe"
$PROJECT_ROOT = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

Write-Host ""
Write-Host "=============================================================" -ForegroundColor Cyan
Write-Host "  Phase V — DigitalOcean Quick Deploy" -ForegroundColor Cyan
Write-Host "=============================================================" -ForegroundColor Cyan
Write-Host ""

# --- Step 1: Check doctl ---
if (-not (Test-Path $DOCTL)) {
    Write-Host "ERROR: doctl not found. Install with: winget install DigitalOcean.Doctl" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] doctl found" -ForegroundColor Green

# --- Step 2: Authenticate ---
Write-Host ""
Write-Host "Step 1: Authenticate with DigitalOcean" -ForegroundColor Yellow
Write-Host "Go to: https://cloud.digitalocean.com/account/api/tokens"
Write-Host "Create a token with Read+Write access, then paste it below:"
Write-Host ""
$token = Read-Host "DigitalOcean API Token"

if ([string]::IsNullOrWhiteSpace($token)) {
    Write-Host "ERROR: No token provided" -ForegroundColor Red
    exit 1
}

$env:DIGITALOCEAN_ACCESS_TOKEN = $token

# Verify auth
Write-Host "Verifying authentication..." -ForegroundColor Yellow
try {
    $result = & $DOCTL account get --access-token $token 2>&1
    if ($LASTEXITCODE -ne 0) { throw $result }
    Write-Host "[OK] Authenticated successfully" -ForegroundColor Green
    Write-Host $result
} catch {
    Write-Host "ERROR: Authentication failed. Check your token." -ForegroundColor Red
    Write-Host $_
    exit 1
}

# --- Step 3: Create DOKS Cluster ---
$CLUSTER_NAME = "todo-app-doks"
$REGION = "nyc1"
$NODE_SIZE = "s-2vcpu-4gb"

Write-Host ""
Write-Host "Step 2: Creating DOKS Kubernetes cluster..." -ForegroundColor Yellow
Write-Host "  Cluster: $CLUSTER_NAME | Region: $REGION | Size: $NODE_SIZE x 1"
Write-Host "  This takes ~5 minutes..."
Write-Host ""

$existing = & $DOCTL kubernetes cluster get $CLUSTER_NAME --access-token $token 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Cluster already exists, skipping creation" -ForegroundColor Green
} else {
    & $DOCTL kubernetes cluster create $CLUSTER_NAME `
        --region $REGION `
        --size $NODE_SIZE `
        --count 1 `
        --access-token $token `
        --wait
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Cluster creation failed" -ForegroundColor Red
        exit 1
    }
    Write-Host "[OK] Cluster created" -ForegroundColor Green
}

# --- Step 4: Save kubeconfig ---
Write-Host ""
Write-Host "Step 3: Configuring kubectl..." -ForegroundColor Yellow
& $DOCTL kubernetes cluster kubeconfig save $CLUSTER_NAME --access-token $token
Write-Host "[OK] kubectl configured" -ForegroundColor Green

# --- Step 5: Install NGINX Ingress ---
Write-Host ""
Write-Host "Step 4: Installing NGINX Ingress Controller..." -ForegroundColor Yellow

$ingressCheck = helm status ingress-nginx -n ingress-nginx 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] NGINX Ingress already installed" -ForegroundColor Green
} else {
    helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx 2>$null
    helm repo update 2>$null
    helm install ingress-nginx ingress-nginx/ingress-nginx `
        --create-namespace `
        --namespace ingress-nginx `
        --set controller.replicaCount=1 `
        --set controller.service.type=LoadBalancer `
        --wait
    Write-Host "[OK] NGINX Ingress installed" -ForegroundColor Green
}

# --- Step 6: Wait for Load Balancer IP ---
Write-Host ""
Write-Host "Step 5: Waiting for Load Balancer IP..." -ForegroundColor Yellow

$externalIP = ""
for ($i = 0; $i -lt 30; $i++) {
    $externalIP = kubectl get svc -n ingress-nginx ingress-nginx-controller -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>$null
    if ($externalIP) { break }
    Write-Host "  Waiting for IP... ($($i+1)/30)" -ForegroundColor Gray
    Start-Sleep -Seconds 10
}

if (-not $externalIP) {
    Write-Host "WARNING: IP not assigned yet. Check later:" -ForegroundColor Yellow
    Write-Host "  kubectl get svc -n ingress-nginx ingress-nginx-controller"
} else {
    Write-Host "[OK] Load Balancer IP: $externalIP" -ForegroundColor Green
}

# --- Step 7: Create namespace + apply manifests ---
Write-Host ""
Write-Host "Step 6: Deploying application..." -ForegroundColor Yellow

kubectl create namespace todo-app 2>$null
kubectl create namespace monitoring 2>$null

# Create minimal secrets (placeholder values for demo)
kubectl create secret generic db-secrets -n todo-app --from-literal=connection-string="placeholder" --dry-run=client -o yaml | kubectl apply -f - 2>$null
kubectl create secret generic jwt-secrets -n todo-app --from-literal=secret-key="phase5-demo-secret-key-2026" --dry-run=client -o yaml | kubectl apply -f - 2>$null
kubectl create secret generic openai-secrets -n todo-app --from-literal=api-key="placeholder" --dry-run=client -o yaml | kubectl apply -f - 2>$null
kubectl create secret generic kafka-secrets -n todo-app --from-literal=brokers="placeholder" --from-literal=sasl-username="placeholder" --from-literal=sasl-password="placeholder" --dry-run=client -o yaml | kubectl apply -f - 2>$null

# Apply DO kustomization
kubectl apply -k "$PROJECT_ROOT\k8s\digitalocean\" 2>&1
Write-Host "[OK] Manifests applied" -ForegroundColor Green

# --- Step 8: Output URL ---
Write-Host ""
Write-Host "=============================================================" -ForegroundColor Green
Write-Host "  DEPLOYMENT COMPLETE" -ForegroundColor Green
Write-Host "=============================================================" -ForegroundColor Green
Write-Host ""
if ($externalIP) {
    Write-Host "  PUBLISHED APP URL:  http://$externalIP" -ForegroundColor White -BackgroundColor DarkGreen
    Write-Host ""
    Write-Host "  API:       http://$externalIP/api" -ForegroundColor Cyan
    Write-Host "  Chat:      http://$externalIP/api/chat" -ForegroundColor Cyan
    Write-Host "  WebSocket: ws://$externalIP/ws" -ForegroundColor Cyan
} else {
    Write-Host "  Run this to get your URL:" -ForegroundColor Yellow
    Write-Host "  kubectl get svc -n ingress-nginx ingress-nginx-controller"
}
Write-Host ""
Write-Host "  Cost: FREE (covered by `$200 credit)" -ForegroundColor Green
Write-Host ""
Write-Host "  Teardown when done:" -ForegroundColor Gray
Write-Host "  & '$DOCTL' kubernetes cluster delete $CLUSTER_NAME --force --access-token <token>" -ForegroundColor Gray
Write-Host "=============================================================" -ForegroundColor Green
