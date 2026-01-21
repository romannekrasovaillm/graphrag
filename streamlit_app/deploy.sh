#!/bin/bash
# GraphRAG Knowledge Base - Deployment Script for Ubuntu/Debian VM

set -e

echo "=========================================="
echo "GraphRAG Knowledge Base - Setup Script"
echo "=========================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${YELLOW}Warning: Running as root. Consider using a non-root user.${NC}"
fi

# 1. Update system
echo -e "\n${GREEN}[1/7] Updating system packages...${NC}"
sudo apt-get update && sudo apt-get upgrade -y

# 2. Install Python 3.11+
echo -e "\n${GREEN}[2/7] Installing Python 3.11...${NC}"
sudo apt-get install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv python3.11-dev python3-pip

# 3. Install system dependencies
echo -e "\n${GREEN}[3/7] Installing system dependencies...${NC}"
sudo apt-get install -y \
    build-essential \
    curl \
    git \
    nginx \
    certbot \
    python3-certbot-nginx

# 4. Create project directory
echo -e "\n${GREEN}[4/7] Setting up project directory...${NC}"
PROJECT_DIR="$HOME/graphrag-app"
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# Copy app files (assuming they're in current directory)
if [ -d "./streamlit_app" ]; then
    cp -r ./streamlit_app/* "$PROJECT_DIR/"
fi

# 5. Create virtual environment and install dependencies
echo -e "\n${GREEN}[5/7] Creating virtual environment...${NC}"
python3.11 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

# 6. Create systemd service
echo -e "\n${GREEN}[6/7] Creating systemd service...${NC}"
sudo tee /etc/systemd/system/graphrag.service > /dev/null <<EOF
[Unit]
Description=GraphRAG Knowledge Base Streamlit App
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin"
ExecStart=$PROJECT_DIR/venv/bin/streamlit run app.py --server.port=8501 --server.address=127.0.0.1
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 7. Configure nginx reverse proxy
echo -e "\n${GREEN}[7/7] Configuring nginx...${NC}"
sudo tee /etc/nginx/sites-available/graphrag > /dev/null <<'EOF'
server {
    listen 80;
    server_name _;  # Replace with your domain

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }

    # WebSocket support for Streamlit
    location /_stcore/stream {
        proxy_pass http://127.0.0.1:8501/_stcore/stream;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/graphrag /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx

# Enable and start services
sudo systemctl daemon-reload
sudo systemctl enable graphrag
sudo systemctl start graphrag

echo -e "\n${GREEN}=========================================="
echo "Setup Complete!"
echo "==========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Create .env file with API keys:"
echo "   nano $PROJECT_DIR/.env"
echo ""
echo "2. Add your keys:"
echo "   DEEPSEEK_API_KEY=sk-..."
echo "   EMBEDDING_API_KEY=..."
echo ""
echo "3. Restart the service:"
echo "   sudo systemctl restart graphrag"
echo ""
echo "4. Access the app:"
echo "   http://YOUR_SERVER_IP"
echo ""
echo "5. (Optional) Setup SSL with certbot:"
echo "   sudo certbot --nginx -d yourdomain.com"
echo ""
echo "Useful commands:"
echo "  View logs:    sudo journalctl -u graphrag -f"
echo "  Restart:      sudo systemctl restart graphrag"
echo "  Stop:         sudo systemctl stop graphrag"
