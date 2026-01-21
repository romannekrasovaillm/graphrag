"""
Chat component for GraphRAG interface
"""

import streamlit as st
import asyncio


def render_chat():
    """Render the chat interface"""
    service = st.session_state.service

    # Chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Input
    if prompt := st.chat_input(
        "Ask a question about your documents...",
        disabled=not st.session_state.index_ready
    ):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate response
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            full_response = ""

            with st.spinner("Thinking..."):
                # Run async query
                async def get_response():
                    nonlocal full_response
                    try:
                        async for chunk in service.query(
                            prompt,
                            method=st.session_state.current_method
                        ):
                            full_response += chunk
                            response_placeholder.markdown(full_response + "▌")
                    except Exception as e:
                        full_response = f"Error: {str(e)}"

                asyncio.run(get_response())

            response_placeholder.markdown(full_response)

        # Save assistant message
        st.session_state.messages.append({
            "role": "assistant",
            "content": full_response
        })


def render_query_settings():
    """Render query method settings"""
    st.subheader("Query Settings")

    method = st.selectbox(
        "Search Method",
        options=["local", "global", "drift", "basic"],
        index=["local", "global", "drift", "basic"].index(
            st.session_state.current_method
        ),
        help="""
        - **Local**: Best for specific questions about entities
        - **Global**: Best for summarization across all documents
        - **Drift**: Combines global and local search
        - **Basic**: Simple vector search (baseline)
        """
    )
    st.session_state.current_method = method

    # Method-specific settings
    if method == "local":
        st.number_input(
            "Top K Entities",
            min_value=1,
            max_value=50,
            value=10,
            key="local_top_k"
        )
    elif method == "global":
        st.slider(
            "Community Level",
            min_value=0,
            max_value=3,
            value=1,
            key="global_level"
        )

    # Clear chat button
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()
