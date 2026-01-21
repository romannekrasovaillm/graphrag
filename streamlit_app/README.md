# GraphRAG Knowledge Base

Streamlit-based interface for Microsoft GraphRAG with DeepSeek API and Ollama local embeddings.

## Quick Start

### 1. Install Ollama (local embeddings)

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull nomic-embed-text
```

### 2. Clone and setup

```bash
git clone -b claude/rag-system-analysis-12wV0 https://github.com/romannekrasovaillm/graphrag.git ~/graphrag-kb
cd ~/graphrag-kb/streamlit_app
pip install -r requirements.txt
```

### 3. Run

```bash
export DEEPSEEK_API_KEY="sk-your-key"
ollama serve &
streamlit run app.py --server.port=8501
```

Open http://localhost:8501

## One-liner for Vast.ai / VM

```bash
cd /workspace && ollama serve &>/dev/null & sleep 2 && export DEEPSEEK_API_KEY="sk-your-key" && pkill -f streamlit; pkill -f cloudflared; cd ~/graphrag-kb/streamlit_app && streamlit run app.py --server.port=8501 --server.address=0.0.0.0 &>/dev/null & sleep 3 && cloudflared tunnel --url http://localhost:8501
```

## Features

- **Chat Interface**: Ask questions about your documents
- **4 Search Methods**: Local, Global, Drift, Basic
- **Document Upload**: Support for .txt, .csv, .json, .docx
- **Index Management**: Build, update, clear indexes
- **Local Embeddings**: Ollama (nomic-embed-text) - free & fast

## Requirements

| Component | Purpose | Cost |
|-----------|---------|------|
| DeepSeek API | LLM for extraction & chat | ~$1-2 per 500 docs |
| Ollama | Local embeddings | Free |

## Search Methods

| Method | Best For | Speed |
|--------|----------|-------|
| **Local** | Specific questions about entities | Fast |
| **Global** | Summarization, themes | Slow |
| **Drift** | Complex multi-part questions | Medium |
| **Basic** | Simple similarity search | Fastest |

## Architecture

```
streamlit_app/
├── app.py                    # Main Streamlit app
├── components/
│   ├── chat.py               # Chat interface
│   └── sidebar.py            # Settings sidebar
├── services/
│   └── graphrag_service.py   # GraphRAG wrapper
├── requirements.txt
└── README.md
```

## Configuration

Default settings use:
- **Chat model**: DeepSeek (`deepseek-chat`)
- **Embeddings**: Ollama (`nomic-embed-text`)

Settings are stored in `~/graphrag_project/settings.yaml`

## Troubleshooting

### Ollama not running

```bash
ollama serve &
ollama pull nomic-embed-text
```

### Indexing hangs

Check if Ollama is responding:
```bash
curl http://localhost:11434/v1/embeddings -d '{"model":"nomic-embed-text","input":"test"}' -H "Content-Type: application/json"
```

### DeepSeek API error

Verify your API key:
```bash
curl https://api.deepseek.com/chat/completions \
  -H "Authorization: Bearer $DEEPSEEK_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-chat","messages":[{"role":"user","content":"Hi"}]}'
```

## License

MIT
