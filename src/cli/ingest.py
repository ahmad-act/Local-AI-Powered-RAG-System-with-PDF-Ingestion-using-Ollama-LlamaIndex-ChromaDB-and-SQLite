# rag_system\cli\ingest.py
import logging
import os
import argparse
from src.config.logging_config import setup_logging
from src.ingestion.pdf_loader import load_pdf
from src.vectorstore.index_manager import IndexManager

setup_logging()
logger = logging.getLogger(__name__)

index_manager = IndexManager()

def ingest_folder(folder: str):
    if not os.path.isdir(folder):
        logger.error(f"Provided path is not a directory: {folder}")
        raise ValueError(f"Path {folder} is not a directory")

    all_docs = []
    for filename in os.listdir(folder):
        if not filename.lower().endswith(".pdf"):
            logger.warning(f"Skipping non-PDF file: {filename}")
            continue
        path = os.path.join(folder, filename)
        try:
            docs = load_pdf(path)
            all_docs.extend(docs)
            logger.info(f"Loaded {filename} ({len(docs)} chunks)")
        except Exception as e:
            logger.exception(f"Failed to load {filename}: {e}")

    try:
        index_manager.build_index(all_docs)
        logger.info(f"Ingestion complete: {len(all_docs)} total chunks")
    except Exception as e:
        logger.exception(f"Index build failed: {e}")
        logger.error("Ingestion failed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", required=True, help="Folder with PDFs")
    args = parser.parse_args()

    try:
        ingest_folder(args.path)
    except Exception as e:
        logger.exception(f"CLI ingestion terminated with error: {e}")