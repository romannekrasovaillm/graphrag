"""
GraphRAG Knowledge Base - Streamlit Interface
Main application entry point
"""

import os
import streamlit as st
from pathlib import Path
import sys

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

# Check API keys from environment
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
JINA_API_KEY = os.environ.get("JINA_API_KEY", "")

from services.graphrag_service import GraphRAGService
from components.chat import render_chat
from components.sidebar import render_sidebar

# Page config
st.set_page_config(
    page_title="GraphRAG Knowledge Base",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stChatMessage {
        padding: 1rem;
    }
    .status-box {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .status-ready { background-color: #d4edda; }
    .status-indexing { background-color: #fff3cd; }
    .status-error { background-color: #f8d7da; }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables"""
    defaults = {
        "messages": [],
        "service": None,
        "index_ready": False,
        "indexing_in_progress": False,
        "current_method": "local",
        "project_path": str(Path.home() / "graphrag_project"),
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def main():
    init_session_state()

    # Initialize service
    if st.session_state.service is None:
        st.session_state.service = GraphRAGService(st.session_state.project_path)

    # Sidebar
    render_sidebar()

    # Main content
    st.title("🔬 GraphRAG Knowledge Base")

    # API Keys status
    col1, col2 = st.columns(2)
    with col1:
        if DEEPSEEK_API_KEY:
            st.success("🔑 DeepSeek API: OK")
        else:
            st.error("🔑 DeepSeek API: Missing (set DEEPSEEK_API_KEY)")
    with col2:
        if JINA_API_KEY:
            st.success("🔑 Jina API: OK")
        else:
            st.error("🔑 Jina API: Missing (set JINA_API_KEY)")

    # Status indicator
    if not DEEPSEEK_API_KEY or not JINA_API_KEY:
        st.warning("⚠️ Set API keys as environment variables before running")
    elif st.session_state.indexing_in_progress:
        st.warning("⏳ Indexing in progress...")
    elif st.session_state.index_ready:
        st.success("✅ Index ready - you can start asking questions")
    else:
        st.info("📁 Upload documents and run indexing to start")

    # Chat interface
    render_chat()


if __name__ == "__main__":
    main()
