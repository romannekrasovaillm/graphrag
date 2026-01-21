#!/bin/bash
# GraphRAG Knowledge Base - Quick Install from Git

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}"
echo "╔════════════════════════════════════════════╗"
echo "║  GraphRAG Knowledge Base - Quick Install   ║"
echo "╚════════════════════════════════════════════╝"
echo -e "${NC}"

# Configuration
REPO_URL="https://github.com/romannekrasovaillm/graphrag.git"
BRANCH="claude/rag-system-analysis-12wV0"
INSTALL_DIR="$HOME/graphrag-kb"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dir)
            INSTALL_DIR="$2"
            shift 2
            ;;
        --dev)
            DEV_MODE=1
            shift
            ;;
        *)
            shift
            ;;
    esac
done

echo -e "${GREEN}[1/6]${NC} Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip git curl

# Detect Python version
PYTHON_CMD=""
for py in python3.12 python3.11 python3.10 python3; do
    if command -v $py &> /dev/null; then
        PYTHON_CMD=$py
        break
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo -e "${YELLOW}Python 3.10+ not found. Installing...${NC}"
    sudo apt-get install -y python3
    PYTHON_CMD=python3
fi

echo -e "${GREEN}Using Python: $PYTHON_CMD ($(${PYTHON_CMD} --version))${NC}"

echo -e "${GREEN}[2/6]${NC} Cloning repository..."
if [ -d "$INSTALL_DIR" ]; then
    echo -e "${YELLOW}Directory exists. Pulling latest changes...${NC}"
    cd "$INSTALL_DIR"
    git fetch origin
    git checkout "$BRANCH"
    git pull origin "$BRANCH"
else
    git clone --branch "$BRANCH" --single-branch "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

echo -e "${GREEN}[3/6]${NC} Setting up Python environment..."
cd "$INSTALL_DIR/streamlit_app"
$PYTHON_CMD -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo -e "${GREEN}[4/6]${NC} Creating project directories..."
mkdir -p "$INSTALL_DIR/data/input"
mkdir -p "$INSTALL_DIR/data/output"

echo -e "${GREEN}[5/6]${NC} Creating configuration..."
if [ ! -f "$INSTALL_DIR/streamlit_app/.env" ]; then
    cat > "$INSTALL_DIR/streamlit_app/.env" << 'EOF'
# GraphRAG API Keys
# Get DeepSeek key: https://platform.deepseek.com/
DEEPSEEK_API_KEY=

# Embedding provider (choose one):
# OpenAI: https://platform.openai.com/
# Jina AI (free tier): https://jina.ai/
EMBEDDING_API_KEY=
EOF
    echo -e "${YELLOW}Created .env template. Please add your API keys!${NC}"
fi

echo -e "${GREEN}[6/6]${NC} Creating run script..."
cat > "$INSTALL_DIR/run.sh" << EOF
#!/bin/bash
cd "$INSTALL_DIR/streamlit_app"
source venv/bin/activate
export GRAPHRAG_PROJECT_PATH="$INSTALL_DIR/data"
streamlit run app.py --server.port=8501
EOF
chmod +x "$INSTALL_DIR/run.sh"

# Create systemd service (optional)
cat > /tmp/graphrag.service << EOF
[Unit]
Description=GraphRAG Knowledge Base
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR/streamlit_app
Environment="PATH=$INSTALL_DIR/streamlit_app/venv/bin"
Environment="GRAPHRAG_PROJECT_PATH=$INSTALL_DIR/data"
ExecStart=$INSTALL_DIR/streamlit_app/venv/bin/streamlit run app.py --server.port=8501 --server.address=0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo -e "${CYAN}"
echo "╔════════════════════════════════════════════╗"
echo "║           Installation Complete!           ║"
echo "╚════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo -e "📁 Installed to: ${GREEN}$INSTALL_DIR${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo ""
echo "1. Add your API keys:"
echo -e "   ${CYAN}nano $INSTALL_DIR/streamlit_app/.env${NC}"
echo ""
echo "2. Run the app:"
echo -e "   ${CYAN}$INSTALL_DIR/run.sh${NC}"
echo ""
echo "3. Open in browser:"
echo -e "   ${CYAN}http://localhost:8501${NC}"
echo ""
echo -e "${YELLOW}Optional - Run as system service:${NC}"
echo "   sudo cp /tmp/graphrag.service /etc/systemd/system/"
echo "   sudo systemctl daemon-reload"
echo "   sudo systemctl enable --now graphrag"
echo ""
echo -e "${YELLOW}Upload your documents:${NC}"
echo "   - Via web interface, or"
echo -e "   - Copy to: ${CYAN}$INSTALL_DIR/data/input/${NC}"
echo ""
