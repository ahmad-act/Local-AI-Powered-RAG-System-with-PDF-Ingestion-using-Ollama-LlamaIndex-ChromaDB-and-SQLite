# rag_system/retrieval/query_engine.py
from src.vectorstore.index_manager import IndexManager
from llama_index.core.query_engine import RetrieverQueryEngine
from src.llm.ollama_llm import OllamaLLM
from src.config.app_settings import AppSettings
import logging
from pathlib import Path
from fastapi import HTTPException
from src.ingestion.pdf_loader import load_pdf
from src.config.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

class QueryEngine:
    def __init__(self):
        try:
            self.index_manager = IndexManager()
            self.llm_model = self.index_manager.llm_model
        except Exception as e:
            logger.exception("Failed to initialize QueryEngine.")
            raise RuntimeError("Failed to initialize QueryEngine") from e

    def query(self, question: str, session_id: str = None):
        try:
            if session_id:
                session_folder = Path(f"{AppSettings.SOURCE_DATA}/{session_id}")
                if not session_folder.exists() or not any(session_folder.iterdir()):
                    logger.warning(f"No source data found for session: {session_id}")
                    raise HTTPException(
                        status_code=404,
                        detail=f"No source data found for session ID: {session_id}"
                    )

                logger.info(f"Building index from session folder: {session_folder}")
                
                # Load documents from session folder
                all_documents = []
                for file in session_folder.glob("*.pdf"):
                    docs, _ = load_pdf(str(file))
                    all_documents.extend(docs)

                if not all_documents:
                    raise HTTPException(
                        status_code=404,
                        detail=f"No valid documents found in session: {session_id}"
                    )

                index = self.index_manager.build_index(documents=all_documents)

            else:
                logger.info("Loading global index...")
                index = self.index_manager.build_index()

            # Build retriever and query engine
            retriever = index.as_retriever(similarity_top_k=5)
            query_engine = RetrieverQueryEngine.from_args(retriever)

            # Retrieve context
            nodes = retriever.retrieve(question)
            context = "\n\n".join([n.node.text for n in nodes])
            # issue-> sources = [f"{n.node.metadata.get('filename')}, page {n.node.metadata.get('page')}" for n in nodes]
            # Deduplicate sources while preserving order
            seen = set()
            sources = []
            for n in nodes:
                src = f"{n.node.metadata.get('filename')}, page {n.node.metadata.get('page')}"
                if src not in seen:
                    seen.add(src)
                    sources.append(src)

            # Format and send prompt
            prompt = f"[user] Answer the question based on the context.\n\nContext:\n{context}\n\nQuestion: {question} [assistant]"
            completion = self.llm_model.complete(prompt)
            answer = completion.text

        except HTTPException as http_exc:
            raise http_exc

        except Exception as e:
            logger.exception("Query failed.")
            answer = "Failed to get answer from language model."
            sources = []

        return {
            "answer": answer,
            "sources": sources
        }
    
