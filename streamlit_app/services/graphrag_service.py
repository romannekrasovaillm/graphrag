"""
GraphRAG Service - wrapper for GraphRAG operations
"""

import asyncio
import logging
import os
import shutil
from pathlib import Path
from typing import AsyncGenerator
import yaml

logger = logging.getLogger(__name__)

# API keys from environment
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
JINA_API_KEY = os.environ.get("JINA_API_KEY", "")


class GraphRAGService:
    """Service class for GraphRAG operations"""

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.input_path = self.project_path / "input"
        self.output_path = self.project_path / "output"
        self.settings_path = self.project_path / "settings.yaml"
        self._ensure_directories()

    def _ensure_directories(self):
        """Create necessary directories"""
        self.project_path.mkdir(parents=True, exist_ok=True)
        self.input_path.mkdir(exist_ok=True)
        self.output_path.mkdir(exist_ok=True)

    def is_index_ready(self) -> bool:
        """Check if index exists and is ready"""
        artifacts = self.output_path / "artifacts"
        if not artifacts.exists():
            return False
        # Check for essential files
        required = ["entities.parquet", "communities.parquet"]
        return all((artifacts / f).exists() for f in required)

    def get_document_count(self) -> int:
        """Count documents in input folder"""
        if not self.input_path.exists():
            return 0
        extensions = [".txt", ".csv", ".json"]
        return sum(1 for f in self.input_path.iterdir()
                   if f.suffix.lower() in extensions)

    def add_documents(self, files: list) -> int:
        """Add uploaded documents to input folder"""
        added = 0
        for file in files:
            # Handle docx conversion
            if file.name.endswith(".docx"):
                text = self._convert_docx(file)
                output_file = self.input_path / f"{Path(file.name).stem}.txt"
                output_file.write_text(text, encoding="utf-8")
            else:
                # Direct copy for txt/csv/json
                output_file = self.input_path / file.name
                output_file.write_bytes(file.getvalue())
            added += 1
        return added

    def _convert_docx(self, file) -> str:
        """Convert docx file to text"""
        try:
            from docx import Document
            import io
            doc = Document(io.BytesIO(file.getvalue()))
            return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except ImportError:
            raise ImportError("python-docx is required for .docx files. Install with: pip install python-docx")

    def get_settings(self) -> dict:
        """Load current settings"""
        if self.settings_path.exists():
            with open(self.settings_path) as f:
                return yaml.safe_load(f)
        return self._default_settings()

    def save_settings(self, settings: dict):
        """Save settings to file"""
        with open(self.settings_path, "w") as f:
            yaml.dump(settings, f, default_flow_style=False, allow_unicode=True)

    def _default_settings(self) -> dict:
        """Default settings template for DeepSeek + Jina"""
        # Get API keys at call time (not module load time)
        deepseek_key = os.environ.get("DEEPSEEK_API_KEY", "")
        jina_key = os.environ.get("JINA_API_KEY", "")

        return {
            "models": {
                "default_chat_model": {
                    "type": "openai_chat",
                    "api_key": "${DEEPSEEK_API_KEY}",
                    "model": "deepseek/deepseek-chat",
                    "api_base": "https://api.deepseek.com/v1",
                    "model_supports_json": True,
                    "request_timeout": 300,
                    "tokens_per_minute": 100000,
                    "requests_per_minute": 500,
                    "concurrent_requests": 10,
                    "max_retries": 3,
                    "retry_wait_seconds": 5,
                },
                "default_embedding_model": {
                    "type": "openai_embedding",
                    "api_key": "${JINA_API_KEY}",
                    "model": "jina-embeddings-v3",
                    "api_base": "https://api.jina.ai/v1",
                }
            },
            "input": {
                "file_type": "text",
                "storage": {
                    "type": "file",
                    "base_dir": "./input"
                }
            },
            "chunks": {
                "size": 1200,
                "overlap": 100
            },
            "extract_graph": {
                "model_id": "default_chat_model",
                "entity_types": ["person", "organization", "concept", "method", "dataset"],
                "max_gleanings": 1
            },
            "community_reports": {
                "model_id": "default_chat_model",
                "max_length": 2000
            },
            "embed_text": {
                "model_id": "default_embedding_model"
            }
        }

    async def run_indexing(self, method: str = "standard", on_progress=None) -> bool:
        """
        Run GraphRAG indexing

        Args:
            method: 'standard' or 'fast'
            on_progress: callback for progress updates
        """
        import subprocess

        cmd = [
            "graphrag", "index",
            "--root", str(self.project_path),
            "--method", method
        ]

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=str(self.project_path)
            )

            async for line in process.stdout:
                decoded = line.decode().strip()
                if on_progress and decoded:
                    on_progress(decoded)
                logger.info(decoded)

            await process.wait()
            return process.returncode == 0

        except Exception as e:
            logger.error(f"Indexing failed: {e}")
            if on_progress:
                on_progress(f"Error: {e}")
            return False

    async def query(
        self,
        question: str,
        method: str = "local",
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Query the knowledge base with streaming response

        Args:
            question: The question to ask
            method: 'local', 'global', 'drift', or 'basic'
            **kwargs: Additional parameters (top_k, etc.)
        """
        # Import here to avoid loading everything at startup
        try:
            from graphrag.api import query as graphrag_query
            from graphrag.config.load_config import load_config
            from graphrag.utils.storage import load_table_from_storage

            config = load_config(self.project_path)

            # Run query
            result = await graphrag_query(
                config=config,
                root=self.project_path,
                method=method,
                query=question,
                streaming=True
            )

            # Stream response
            async for chunk in result:
                yield chunk

        except ImportError:
            # Fallback to CLI if API not available
            async for chunk in self._query_via_cli(question, method):
                yield chunk

    async def _query_via_cli(
        self,
        question: str,
        method: str
    ) -> AsyncGenerator[str, None]:
        """Fallback: query via CLI"""
        import subprocess

        cmd = [
            "graphrag", "query",
            "--root", str(self.project_path),
            "--method", method,
            question
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(self.project_path)
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            yield f"Error: {stderr.decode()}"
        else:
            yield stdout.decode()

    def clear_index(self):
        """Clear the current index"""
        if self.output_path.exists():
            shutil.rmtree(self.output_path)
            self.output_path.mkdir()

    def clear_documents(self):
        """Clear all input documents"""
        if self.input_path.exists():
            shutil.rmtree(self.input_path)
            self.input_path.mkdir()

    def get_index_stats(self) -> dict:
        """Get statistics about the current index"""
        stats = {
            "documents": self.get_document_count(),
            "entities": 0,
            "relationships": 0,
            "communities": 0,
            "indexed": self.is_index_ready()
        }

        artifacts = self.output_path / "artifacts"
        if artifacts.exists():
            try:
                import pandas as pd

                entities_file = artifacts / "entities.parquet"
                if entities_file.exists():
                    stats["entities"] = len(pd.read_parquet(entities_file))

                rels_file = artifacts / "relationships.parquet"
                if rels_file.exists():
                    stats["relationships"] = len(pd.read_parquet(rels_file))

                comm_file = artifacts / "communities.parquet"
                if comm_file.exists():
                    stats["communities"] = len(pd.read_parquet(comm_file))

            except Exception as e:
                logger.warning(f"Could not read stats: {e}")

        return stats
