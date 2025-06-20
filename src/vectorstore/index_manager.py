# rag_system/vectorstore/index_manager.py
from llama_index.core import VectorStoreIndex, Settings, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from chromadb import PersistentClient
from src.embedding.ollama_embedder import OllamaEmbedding
from src.llm.ollama_llm import OllamaLLM
from src.config.app_settings import AppSettings
import logging
from src.config.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

class IndexManager:
    def __init__(self):
        try:
            self.client = PersistentClient(path=AppSettings.CHROMA_DB)
            self.collection = self.client.get_or_create_collection(name="rag_collection")
            self.vector_store = ChromaVectorStore(chroma_collection=self.collection)

            # Instantiate embedding model with nomic-embed-text
            self.embed_model = OllamaEmbedding(model=AppSettings.EMBED_MODEL)
            # Instantiate LLM model with deepseek-r1:1.5b
            self.llm_model = OllamaLLM(model=AppSettings.QA_MODEL)

            Settings.embed_model = self.embed_model
            Settings.llm = self.llm_model

            logger.info("IndexManager initialized successfully.")
        except Exception as e:
            logger.exception(f"Failed to initialize IndexManager.")
            raise RuntimeError("Initialization failed for IndexManager") from e

    def build_index(self, documents=None):
        try:
            storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
            if documents:
                logger.info(f"Building index from {len(documents)} documents.")
                index = VectorStoreIndex.from_documents(
                    documents,
                    storage_context=storage_context,
                )
                logger.info("Index successfully built from documents.")
            else:
                logger.info("Loading index from existing vector store.")
                index = VectorStoreIndex.from_vector_store(
                    vector_store=self.vector_store,
                    storage_context=storage_context,
                )
                logger.info("Index successfully loaded from vector store.")
            return index
        except Exception as e:
            logger.exception(f"Error while building/loading index.")
            raise RuntimeError("Failed to build/load index.") from e
        

    # def get_all_doc_ids(self) -> set:
    #     try:
    #         results = self.collection.get(include=["documents"])
    #         return set(results["ids"])
    #     except Exception as e:
    #         logger.exception(f"Failed to fetch existing document IDs.")
    #         return set()

    def get_all_file_hashes(self) -> set:
        try:
            results = self.collection.get(include=["metadatas"])
            file_hashes = {
                meta.get("file_hash") for meta in results.get("metadatas", []) if "file_hash" in meta
            }
            return file_hashes
        except Exception as e:
            logger.exception("Failed to fetch file-level hashes.")
            return set()
