#!/bin/bash
set -e

echo "=== Requirements Gatherer — Demo Setup ==="

# Install Docker
sudo dnf install -y docker git curl
sudo systemctl enable --now docker
sudo usermod -aG docker ec2-user

# Install Docker Compose plugin
sudo mkdir -p /usr/local/lib/docker/cli-plugins
sudo curl -fsSL https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64 \
  -o /usr/local/lib/docker/cli-plugins/docker-compose
sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

# Clone the repo
git clone https://github.com/PythonFunFactory/AppRequirementsGatherer.git
cd AppRequirementsGatherer
git checkout Demo

# Get Anthropic API key
read -rp "Paste your Anthropic API key: " ANTHROPIC_KEY

# Get the public IP of this instance
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)

# Write .env
cat > .env <<EOF
DEV_AUTH=true
ANTHROPIC_API_KEY=${ANTHROPIC_KEY}
SECRET_KEY=$(openssl rand -hex 32)
ADMIN_EMAILS=admin@demo.local
FRONTEND_URL=http://${PUBLIC_IP}
DATABASE_URL=sqlite:////app/data/app.db
PDF_STORAGE_PATH=./static/pdfs
EOF

# Build and start
sudo docker compose up -d --build

echo ""
echo "================================================"
echo " App is live at: http://${PUBLIC_IP}"
echo " Sign in with any email address (dev mode)"
echo "================================================"
