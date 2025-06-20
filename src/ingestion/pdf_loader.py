# rag_system\ingestion\pdf_loader.py
import logging
import fitz  # PyMuPDF
import hashlib
from llama_index.core.schema import Document
from src.config.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

def compute_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def load_pdf(path: str) -> tuple[list[Document], str]:
    doc = None
    try:
        doc = fitz.open(path)
        chunks = []
        full_text = ""

        for page_num, page in enumerate(doc):
            text = page.get_text()
            if not text.strip():
                continue
            full_text += text
            page_hash = compute_hash(text)
            metadata = {
                "filename": path.split("/")[-1],
                "page": page_num + 1,
                "hash": page_hash,
            }
            chunks.append(Document(text=text, metadata=metadata, doc_id=page_hash))

        file_hash = compute_hash(full_text)
        logger.info("Loaded %d chunks from PDF: %s", len(chunks), path)
        return chunks, file_hash
    except Exception as e:
        logger.exception("Failed to load PDF: %s", path)
        raise RuntimeError(f"Failed to load PDF {path}: {e}") from e
    finally:
        if doc:
            doc.close()
