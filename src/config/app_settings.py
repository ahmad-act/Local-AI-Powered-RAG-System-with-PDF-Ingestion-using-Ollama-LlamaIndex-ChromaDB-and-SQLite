# rag_system\config\app_settings.py
import os
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class AppSettings:
    EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")  # embedding model
    QA_MODEL = os.getenv("QA_MODEL", "deepseek-r1:1.5b")        # QA model
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    CHROMA_DB = os.getenv("CHROMA_DB", "./chroma_db")
    SESSION_DB = os.getenv("SESSION_DB", "sqlite:///chat.db")
    SOURCE_DATA = os.getenv("SOURCE_DATA", "source-data")
    LOG_DIR = os.getenv("LOG_DIR", "logs")
    LOG_CLEANUP_FILE = os.getenv("LOG_CLEANUP_FILE", "cleanup_log.csv")
     

logger.info("Settings loaded: EMBED_MODEL=%s; QA_MODEL=%s", AppSettings.EMBED_MODEL, AppSettings.QA_MODEL)