"""
Sidebar component with settings and controls
"""

import os
import streamlit as st
import asyncio
from pathlib import Path

# API keys from environment
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")


def render_sidebar():
    """Render the sidebar with all controls"""
    service = st.session_state.service

    with st.sidebar:
        st.header("⚙️ Settings")

        # Tab navigation
        tab = st.radio(
            "Section",
            ["📊 Status", "📁 Documents", "🔧 Index", "⚡ Query"],
            label_visibility="collapsed"
        )

        st.divider()

        if tab == "📊 Status":
            render_status_tab(service)
        elif tab == "📁 Documents":
            render_documents_tab(service)
        elif tab == "🔧 Index":
            render_index_tab(service)
        elif tab == "⚡ Query":
            from components.chat import render_query_settings
            render_query_settings()


def render_status_tab(service):
    """Render status information"""

    # API Keys status
    st.subheader("API & Services")
    if DEEPSEEK_API_KEY:
        st.success(f"DeepSeek: ✅ ...{DEEPSEEK_API_KEY[-8:]}")
    else:
        st.error("DeepSeek: ❌ Not set")

    # Check Ollama
    import requests
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=2)
        if resp.status_code == 200:
            st.success("Ollama: ✅ Running (local embeddings)")
        else:
            st.warning("Ollama: ⚠️ Not responding")
    except:
        st.error("Ollama: ❌ Not running (start with: ollama serve)")

    st.divider()

    # Index status
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


