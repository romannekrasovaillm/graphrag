"""
Sidebar component with settings and controls
"""

import streamlit as st
import asyncio
from pathlib import Path


def render_sidebar():
    """Render the sidebar with all controls"""
    service = st.session_state.service

    with st.sidebar:
        st.header("⚙️ Settings")

        # Tab navigation
        tab = st.radio(
            "Section",
            ["📊 Status", "📁 Documents", "🔧 Index", "🔑 API Keys", "⚡ Query"],
            label_visibility="collapsed"
        )

        st.divider()

        if tab == "📊 Status":
            render_status_tab(service)
        elif tab == "📁 Documents":
            render_documents_tab(service)
        elif tab == "🔧 Index":
            render_index_tab(service)
        elif tab == "🔑 API Keys":
            render_api_keys_tab(service)
        elif tab == "⚡ Query":
            from components.chat import render_query_settings
            render_query_settings()


def render_status_tab(service):
    """Render status information"""
    st.subheader("Index Status")

    stats = service.get_index_stats()

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Documents", stats["documents"])
        st.metric("Entities", stats["entities"])
    with col2:
        st.metric("Relationships", stats["relationships"])
        st.metric("Communities", stats["communities"])

    if stats["indexed"]:
        st.success("✅ Index Ready")
        st.session_state.index_ready = True
    else:
        st.warning("⚠️ Not Indexed")
        st.session_state.index_ready = False


def render_documents_tab(service):
    """Render document management"""
    st.subheader("Upload Documents")

    uploaded_files = st.file_uploader(
        "Choose files",
        type=["txt", "csv", "json", "docx"],
        accept_multiple_files=True,
        help="Supported: .txt, .csv, .json, .docx"
    )

    if uploaded_files:
        if st.button("Add Documents", type="primary"):
            with st.spinner("Processing files..."):
                added = service.add_documents(uploaded_files)
                st.success(f"Added {added} documents")
                st.rerun()

    # Current documents
    st.subheader("Current Documents")
    doc_count = service.get_document_count()
    st.info(f"📄 {doc_count} documents in input folder")

    if doc_count > 0:
        # List files
        with st.expander("View Files"):
            for f in service.input_path.iterdir():
                if f.is_file():
                    st.text(f"• {f.name}")

        if st.button("Clear All Documents", type="secondary"):
            service.clear_documents()
            st.warning("Documents cleared")
            st.rerun()


def render_index_tab(service):
    """Render indexing controls"""
    st.subheader("Indexing")

    # Method selection
    index_method = st.selectbox(
        "Indexing Method",
        ["standard", "fast"],
        help="""
        - **Standard**: Full LLM extraction (more accurate, slower)
        - **Fast**: NLP + LLM hybrid (faster, cheaper)
        """
    )

    # Entity types for extraction
    st.subheader("Entity Types")
    default_types = ["person", "organization", "concept", "method", "dataset"]
    entity_types = st.multiselect(
        "Types to extract",
        options=["person", "organization", "location", "event",
                 "concept", "method", "dataset", "metric", "technology"],
        default=default_types
    )

    # Chunk settings
    st.subheader("Chunk Settings")
    chunk_size = st.slider("Chunk Size (tokens)", 500, 2000, 1200)
    chunk_overlap = st.slider("Chunk Overlap (tokens)", 0, 200, 100)

    # Update settings
    if st.button("Save Settings"):
        settings = service.get_settings()
        settings["chunks"]["size"] = chunk_size
        settings["chunks"]["overlap"] = chunk_overlap
        settings["extract_graph"]["entity_types"] = entity_types
        service.save_settings(settings)
        st.success("Settings saved")

    st.divider()

    # Run indexing
    col1, col2 = st.columns(2)

    with col1:
        if st.button("▶️ Run Indexing", type="primary",
                     disabled=st.session_state.indexing_in_progress):
            run_indexing(service, index_method)

    with col2:
        if st.button("🔄 Update Index",
                     disabled=st.session_state.indexing_in_progress or not service.is_index_ready()):
            run_indexing(service, f"{index_method}_update")

    # Clear index
    if service.is_index_ready():
        if st.button("🗑️ Clear Index"):
            service.clear_index()
            st.session_state.index_ready = False
            st.warning("Index cleared")
            st.rerun()


def run_indexing(service, method):
    """Run indexing with progress display"""
    st.session_state.indexing_in_progress = True

    progress_container = st.empty()
    log_container = st.empty()

    logs = []

    def on_progress(msg):
        logs.append(msg)
        # Keep last 10 lines
        log_container.code("\n".join(logs[-10:]), language="")

    async def do_index():
        success = await service.run_indexing(
            method=method.replace("_update", ""),
            on_progress=on_progress
        )
        return success

    with st.spinner(f"Running {method} indexing..."):
        success = asyncio.run(do_index())

    st.session_state.indexing_in_progress = False

    if success:
        st.success("✅ Indexing completed!")
        st.session_state.index_ready = True
    else:
        st.error("❌ Indexing failed. Check logs above.")

    st.rerun()


def render_api_keys_tab(service):
    """Render API key configuration"""
    st.subheader("API Configuration")

    # Load current .env if exists
    env_path = service.project_path / ".env"
    current_env = {}
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                key, val = line.split("=", 1)
                current_env[key.strip()] = val.strip()

    # DeepSeek settings
    st.markdown("### DeepSeek (Chat Model)")
    deepseek_key = st.text_input(
        "DEEPSEEK_API_KEY",
        value=current_env.get("DEEPSEEK_API_KEY", ""),
        type="password"
    )

    # Embedding provider selection
    st.markdown("### Embedding Model")
    embed_provider = st.selectbox(
        "Provider",
        ["OpenAI", "Jina AI", "VoyageAI", "Local (Ollama)"]
    )

    if embed_provider == "OpenAI":
        embed_key = st.text_input(
            "OPENAI_API_KEY",
            value=current_env.get("OPENAI_API_KEY", ""),
            type="password"
        )
        embed_env_name = "OPENAI_API_KEY"
    elif embed_provider == "Jina AI":
        embed_key = st.text_input(
            "JINA_API_KEY",
            value=current_env.get("JINA_API_KEY", ""),
            type="password"
        )
        embed_env_name = "JINA_API_KEY"
        st.info("Jina offers 1M free tokens")
    elif embed_provider == "VoyageAI":
        embed_key = st.text_input(
            "VOYAGE_API_KEY",
            value=current_env.get("VOYAGE_API_KEY", ""),
            type="password"
        )
        embed_env_name = "VOYAGE_API_KEY"
    else:
        embed_key = ""
        embed_env_name = ""
        st.info("Configure Ollama URL in settings.yaml")

    # Save button
    if st.button("Save API Keys", type="primary"):
        env_content = f"""# GraphRAG API Keys
DEEPSEEK_API_KEY={deepseek_key}
EMBEDDING_API_KEY={embed_key}
"""
        env_path.write_text(env_content)

        # Update settings.yaml with correct embedding provider
        settings = service.get_settings()
        if embed_provider == "OpenAI":
            settings["models"]["default_embedding_model"]["model_provider"] = "openai"
            settings["models"]["default_embedding_model"]["model"] = "text-embedding-3-small"
        elif embed_provider == "Jina AI":
            settings["models"]["default_embedding_model"]["model_provider"] = "jina_ai"
            settings["models"]["default_embedding_model"]["model"] = "jina-embeddings-v3"
        elif embed_provider == "VoyageAI":
            settings["models"]["default_embedding_model"]["model_provider"] = "voyage"
            settings["models"]["default_embedding_model"]["model"] = "voyage-2"

        service.save_settings(settings)
        st.success("Configuration saved!")
