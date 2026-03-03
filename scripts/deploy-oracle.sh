#!/usr/bin/env bash
###############################################################################
# deploy-oracle.sh — Deploy to Oracle Cloud Free Tier ARM A1 VM
#
# Usage:
#   bash scripts/deploy-oracle.sh <PUBLIC_IP> [SSH_KEY_PATH] [SSH_USER]
#
# Example:
#   bash scripts/deploy-oracle.sh 129.153.x.x ~/.ssh/oracle_key ubuntu
###############################################################################
set -euo pipefail

# ── Arguments ──
PUBLIC_IP="${1:?Usage: deploy-oracle.sh <PUBLIC_IP> [SSH_KEY_PATH] [SSH_USER]}"
SSH_KEY="${2:-~/.ssh/id_rsa}"
SSH_USER="${3:-ubuntu}"
REMOTE_DIR="/opt/todo-app"
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# ── Colors ──
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log()  { echo -e "${CYAN}[$(date +%H:%M:%S)]${NC} $*"; }
ok()   { echo -e "${GREEN}[✓]${NC} $*"; }
warn() { echo -e "${YELLOW}[!]${NC} $*"; }
err()  { echo -e "${RED}[✗]${NC} $*"; exit 1; }

SSH_CMD="ssh -i $SSH_KEY -o StrictHostKeyChecking=no -o ConnectTimeout=10 ${SSH_USER}@${PUBLIC_IP}"
SCP_CMD="scp -i $SSH_KEY -o StrictHostKeyChecking=no"

echo ""
echo "============================================"
echo "  Oracle Cloud Free Tier Deployment"
echo "============================================"
echo "  Target: ${SSH_USER}@${PUBLIC_IP}"
echo "  Remote: ${REMOTE_DIR}"
echo "============================================"
echo ""

###############################################################################
# Phase 1: Validate SSH connectivity
###############################################################################
log "Phase 1/8: Validating SSH connectivity..."

if $SSH_CMD "echo 'SSH OK'" &>/dev/null; then
    ok "SSH connection successful"
else
    err "Cannot connect to ${SSH_USER}@${PUBLIC_IP}. Check IP, key, and security list."
fi

# Detect OS
REMOTE_OS=$($SSH_CMD "cat /etc/os-release 2>/dev/null | grep ^ID= | cut -d= -f2 | tr -d '\"'" || echo "unknown")
log "Detected OS: $REMOTE_OS"

###############################################################################
# Phase 2: Install Docker Engine + dependencies
###############################################################################
log "Phase 2/8: Installing Docker..."

$SSH_CMD bash <<'INSTALL_DOCKER'
set -euo pipefail

if command -v docker &>/dev/null; then
    echo "Docker already installed: $(docker --version)"
    exit 0
fi

# Detect package manager
if command -v apt-get &>/dev/null; then
    # Ubuntu / Debian
    sudo apt-get update -y
    sudo apt-get install -y ca-certificates curl gnupg
    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | \
        sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update -y
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin
elif command -v dnf &>/dev/null; then
    # Oracle Linux / RHEL
    sudo dnf install -y dnf-utils
    sudo dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
    sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin
fi

sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"
echo "Docker installed: $(docker --version)"
INSTALL_DOCKER

ok "Docker installed"

###############################################################################
# Phase 3: Upload project files
###############################################################################
log "Phase 3/8: Uploading project files..."

# Create remote directory
$SSH_CMD "sudo mkdir -p $REMOTE_DIR && sudo chown \$USER:\$USER $REMOTE_DIR"

# Sync project (exclude unnecessary files)
rsync -azP --delete \
    -e "ssh -i $SSH_KEY -o StrictHostKeyChecking=no" \
    --exclude '.git' \
    --exclude 'node_modules' \
    --exclude '.next' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude '.env' \
    --exclude '.specify' \
    --exclude 'history' \
    --exclude 'specs' \
    --exclude 'k8s' \
    --exclude '.vscode' \
    "$PROJECT_ROOT/" "${SSH_USER}@${PUBLIC_IP}:${REMOTE_DIR}/"

ok "Project uploaded to $REMOTE_DIR"

###############################################################################
# Phase 4: Configure environment
###############################################################################
log "Phase 4/8: Configuring environment..."

# Generate a random secret key for production
SECRET_KEY=$(openssl rand -hex 32)

$SSH_CMD bash <<CONFIGURE
set -euo pipefail
cd $REMOTE_DIR

# Create .env for overrides (read by env.sh via defaults)
cat > .env <<EOF
POSTGRES_USER=postgres
POSTGRES_PASSWORD=$(openssl rand -hex 16)
POSTGRES_DB=todo_app
SECRET_KEY=$SECRET_KEY
PUBLIC_IP=$PUBLIC_IP
EOF

# Make scripts executable
chmod +x scripts/oracle/*.sh scripts/deploy-oracle.sh
CONFIGURE

ok "Environment configured"

###############################################################################
# Phase 5: Build and deploy all services
###############################################################################
log "Phase 5/8: Building and deploying services..."

# Source .env on the remote and export, then run start-all
$SSH_CMD bash <<DEPLOY
set -euo pipefail
cd $REMOTE_DIR

# Export .env vars so env.sh picks them up
set -a
source .env
set +a

# Use newgrp to pick up docker group (avoids re-login)
sg docker -c "bash scripts/oracle/start-all.sh"
DEPLOY

ok "All services deployed"

###############################################################################
# Phase 6: Configure firewall
###############################################################################
log "Phase 6/8: Configuring firewall..."

$SSH_CMD bash <<'FIREWALL'
set -euo pipefail

# iptables — open port 80 and 443
if command -v iptables &>/dev/null; then
    sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT 2>/dev/null || true
    sudo iptables -I INPUT -p tcp --dport 443 -j ACCEPT 2>/dev/null || true
fi

# firewalld (Oracle Linux)
if command -v firewall-cmd &>/dev/null; then
    sudo firewall-cmd --permanent --add-port=80/tcp 2>/dev/null || true
    sudo firewall-cmd --permanent --add-port=443/tcp 2>/dev/null || true
    sudo firewall-cmd --reload 2>/dev/null || true
fi

# ufw (Ubuntu)
if command -v ufw &>/dev/null; then
    sudo ufw allow 80/tcp 2>/dev/null || true
    sudo ufw allow 443/tcp 2>/dev/null || true
fi

echo "Firewall rules applied."
FIREWALL

ok "Firewall configured"
warn "REMINDER: Also add Ingress Rules in your OCI VCN Security List:"
warn "  - Port 80 (HTTP) from 0.0.0.0/0"
warn "  - Port 443 (HTTPS) from 0.0.0.0/0"

###############################################################################
# Phase 7: Health check
###############################################################################
log "Phase 7/8: Running health checks..."

sleep 10  # Give services time to fully start

HEALTH_OK=true

# Check via the remote
$SSH_CMD bash <<'HEALTHCHECK' || HEALTH_OK=false
set -euo pipefail
echo "Container status:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | head -20
echo ""

# Check API health
if curl -sf --max-time 5 http://localhost/api/health; then
    echo ""
    echo "API health: OK"
else
    echo "API health: FAIL"
    exit 1
fi
HEALTHCHECK

if [ "$HEALTH_OK" = true ]; then
    ok "Health checks passed"
else
    warn "Health checks had issues — services may still be starting"
    warn "SSH in and run: bash $REMOTE_DIR/scripts/oracle/status.sh"
fi

###############################################################################
# Phase 8: Output
###############################################################################
log "Phase 8/8: Deployment complete!"

echo ""
echo "============================================"
echo "  Deployment Successful!"
echo "============================================"
echo ""
echo "  App URL:    http://${PUBLIC_IP}"
echo "  API Health: http://${PUBLIC_IP}/api/health"
echo ""
echo "  SSH:        ssh -i $SSH_KEY ${SSH_USER}@${PUBLIC_IP}"
echo "  Status:     bash $REMOTE_DIR/scripts/oracle/status.sh"
echo "  Logs:       docker logs <container-name>"
echo "  Stop:       bash $REMOTE_DIR/scripts/oracle/stop-all.sh"
echo "  Restart:    bash $REMOTE_DIR/scripts/oracle/start-all.sh"
echo ""
echo "  Cost: \$0 (Oracle Cloud Always Free Tier)"
echo "============================================"
