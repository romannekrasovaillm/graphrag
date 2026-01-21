# GraphRAG Knowledge Base

Streamlit-based interface for Microsoft GraphRAG with DeepSeek API support.

## Quick Install (One Command)

```bash
curl -sSL https://raw.githubusercontent.com/romannekrasovaillm/graphrag/claude/rag-system-analysis-12wV0/streamlit_app/install.sh | bash
```

Or manually:

```bash
git clone -b claude/rag-system-analysis-12wV0 https://github.com/romannekrasovaillm/graphrag.git
cd graphrag/streamlit_app
chmod +x install.sh
./install.sh
```

## Features

- **Chat Interface**: Ask questions about your documents
- **Multiple Search Methods**: Local, Global, Drift, Basic
- **Document Upload**: Support for .txt, .csv, .json, .docx
- **Index Management**: Build, update, and clear indexes
- **API Configuration**: Easy setup for DeepSeek and embedding providers

## Quick Start (Local)

### 1. Install dependencies

```bash
cd streamlit_app
pip install -r requirements.txt
```

### 2. Set environment variables and run

```bash
export DEEPSEEK_API_KEY="sk-your-deepseek-key"
export JINA_API_KEY="jina_your-jina-key"
streamlit run app.py
```

Open http://localhost:8501

## Deployment on VM

### Option 1: Direct Installation

```bash
# Upload files to VM
scp -r streamlit_app user@your-vm:/home/user/

# SSH into VM
ssh user@your-vm

# Run setup script
cd /home/user/streamlit_app
chmod +x deploy.sh
./deploy.sh
```

### Option 2: Docker

```bash
# Create .env file
echo "DEEPSEEK_API_KEY=sk-..." > .env
echo "EMBEDDING_API_KEY=..." >> .env

# Run with docker-compose
docker-compose up -d
```

## Configuration

### API Keys

| Provider | Environment Variable | Notes |
|----------|---------------------|-------|
| DeepSeek | `DEEPSEEK_API_KEY` | Chat model |
| OpenAI | `OPENAI_API_KEY` | Embeddings (paid) |
| Jina AI | `JINA_API_KEY` | Embeddings (1M free) |
| VoyageAI | `VOYAGE_API_KEY` | Embeddings |

### Search Methods

| Method | Best For | Speed |
|--------|----------|-------|
| **Local** | Specific questions about entities | Fast |
| **Global** | Summarization, themes | Slow |
| **Drift** | Complex multi-part questions | Medium |
| **Basic** | Simple similarity search | Fastest |

### Entity Types (for scientific articles)

Recommended configuration:
```yaml
entity_types:
  - person       # Authors, researchers
  - organization # Universities, companies
  - concept      # Scientific concepts
  - method       # Research methods
  - dataset      # Datasets used
  - metric       # Evaluation metrics
```

## Architecture

```
streamlit_app/
├── app.py                 # Main Streamlit app
├── components/
│   ├── chat.py           # Chat interface
│   └── sidebar.py        # Settings sidebar
├── services/
│   └── graphrag_service.py  # GraphRAG wrapper
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── deploy.sh             # VM deployment script
```

## Cost Estimation

For 500 scientific articles (~5000 pages):

| Component | Cost |
|-----------|------|
| DeepSeek indexing | ~$1-2 |
| OpenAI embeddings | ~$0.50 |
| Jina embeddings | Free (1M tokens) |

## Troubleshooting

### Indexing fails

1. Check API keys in `.env`
2. Verify document format (UTF-8 encoding)
3. Check logs: `sudo journalctl -u graphrag -f`

### WebSocket errors in browser

Ensure nginx is configured for WebSocket:
```nginx
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
```

### Out of memory

- Use `fast` indexing method
- Reduce `chunks.size` in settings
- Add swap: `sudo fallocate -l 4G /swapfile`

## License

MIT
