# rag_system\api\app.py
from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException, Query
from src.ingestion.pdf_loader import load_pdf
from src.vectorstore.index_manager import IndexManager
from src.retrieval.query_engine import QueryEngine
from src.chat.session_store import save_chat, get_history, get_all_history, delete_history
import os
import tempfile
from fastapi.responses import JSONResponse
from typing import Optional
from uuid import uuid4
from pathlib import Path
from src.config.app_settings import AppSettings
import shutil
from datetime import datetime
import csv
import logging
from src.config.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI()
query_engine = QueryEngine()
index_manager = IndexManager()

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url.path} from {request.client.host}")
    try:
        response = await call_next(request)
        return response
    except Exception:
        logger.exception("Request processing failed")
        raise

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error during request processing")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "detail": str(exc)},
    )

@app.post("/ask")
async def ask(
    query: str = Form(...),
    session_id: str = Form(None),
    session_name: str = Form(None)
):
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")

    try:
        # Generate session_id if not provided
        session_id = session_id or str(uuid4())

        # Derive session_name if not provided
        session_name = session_name or query.strip()[:50]

        # Ensure source-data/session_id directory exists
        source_folder = Path(f"{AppSettings.SOURCE_DATA}/{session_id}")
        source_folder.mkdir(parents=True, exist_ok=True)

        # Perform query
        result = query_engine.query(query, session_id)

        # Save chat with optional session name
        save_chat(session_id, query, result["answer"], result["sources"], session_name)

        return {
            "session_id": session_id,
            "session_name": session_name,
            "answer": result["answer"],
            "sources": result["sources"]
        }
    except Exception:
        logger.exception("Query processing failed")
        raise HTTPException(status_code=500, detail="Query failed")
    
@app.post("/ingest")
async def ingest(
    file: UploadFile = File(...),
    session_id: str = Form(None),
    ):

    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    try:
        # with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        #     temp_file.write(await file.read())
        #     temp_file_path = temp_file.name

        # Generate session_id if not provided
        session_id = session_id or str(uuid4())

		# # Check if page-level hash already exists
        # documents = load_pdf(temp_file_path)
        # existing_hashes = index_manager.get_all_doc_ids()
        # new_documents = [doc for doc in documents if doc.doc_id not in existing_hashes]

        # if not new_documents:
        #     logger.info(f"Duplicate file detected: {file.filename}, skipping ingestion.")
        #     os.unlink(temp_file_path)
        #     return {"message": f"Skipped ingestion: {file.filename} already ingested."}

        # Create session folder inside source-data
        session_folder = Path(AppSettings.SOURCE_DATA) / session_id
        session_folder.mkdir(parents=True, exist_ok=True)

        # Define full file path under session folder
        file_path = session_folder / file.filename

        # Save uploaded file to disk
        with open(file_path, "wb") as f:
            f.write(await file.read())

        # Load PDF and get documents + file hash
        documents, file_hash = load_pdf(str(file_path))
														 
        # Check if file-level hash already exists
        existing_file_hashes = index_manager.get_all_file_hashes()
        if file_hash in existing_file_hashes:
            logger.info(f"Duplicate file detected: {file.filename}, skipping ingestion.")
            # # Optionally delete the uploaded duplicate file to save space
            # file_path.unlink()
            # return {
            #     "message": f"Skipped ingestion: {file.filename} already ingested.",
            #     "session_id": session_id
            # }

        # Add file-level hash to each chunk's metadata
        for doc in documents:
            doc.metadata["file_hash"] = file_hash

        # Build index with new documents
        index_manager.build_index(documents)

        return {
            "message": f"Ingested {file.filename} with {len(documents)} pages.",
            "session_id": session_id
        }
    except Exception:
        logger.exception("Ingestion failed")
        raise HTTPException(status_code=500, detail="Ingestion failed")

@app.get("/history/{session_id}")
async def history(session_id: str):
    try:
        records = get_history(session_id)
        return [{"query": r.query, "response": r.response, "sources": r.sources} for r in records]
    except Exception:
        logger.exception("Failed to retrieve chat history")
        raise HTTPException(status_code=500, detail="Failed to retrieve history")

@app.get("/history")
async def all_history():
    try:
        records = get_all_history()
        return [
            {
                "session_id": r.session_id,
                "query": r.query,
                "response": r.response,
                "sources": r.sources
            }
            for r in records
        ]
    except Exception:
        logger.exception("Failed to retrieve all chat history")
        raise HTTPException(status_code=500, detail="Failed to retrieve all history")

@app.delete("/history/{session_id}")
async def delete_session_history(session_id: str):
    try:
        count = delete_history(session_id)
        return {"message": f"Deleted {count} records for session {session_id}"}
    except Exception:
        logger.exception("Failed to delete session history")
        raise HTTPException(status_code=500, detail="Failed to delete session history")

@app.delete("/cleanup-unused-sessions")
async def cleanup_unused_sessions(
    dry_run: bool = Query(False, description="If true, simulate deletions without actually deleting.")
):
    deleted_sessions = []
    simulated_sessions = []

    try:
        source_data_path = Path(AppSettings.SOURCE_DATA)
        if not source_data_path.exists():
            return {"message": "No source-data directory found."}

        for session_folder in source_data_path.iterdir():
            if session_folder.is_dir():
                session_id = session_folder.name

                try:
                    history_records = get_history(session_id)
                    has_history = len(history_records) > 0
                except Exception:
                    has_history = False

                if not has_history:
                    if dry_run:
                        simulated_sessions.append(session_id)
                        logger.info(f"[Dry Run] Would delete: {session_folder}")
                    else:
                        try:
                            shutil.rmtree(session_folder)
                            delete_history(session_id)
                            deleted_sessions.append(session_id)
                            logger.info(f"Deleted unused session folder and history: {session_folder}")
                        except Exception as e:
                            logger.warning(f"Failed to cleanup {session_folder}: {e}")

        if not dry_run and deleted_sessions:
            write_cleanup_log(deleted_sessions)

        return {
            "dry_run": dry_run,
            "message": (
                f"Simulated {len(simulated_sessions)} deletions." if dry_run
                else f"Deleted {len(deleted_sessions)} unused session(s)."
            ),
            "sessions": simulated_sessions if dry_run else deleted_sessions
        }

    except Exception as e:
        logger.exception("Cleanup failed")
        raise HTTPException(
            status_code=500,
            detail="Cleanup failed due to an unexpected error."
        )


def write_cleanup_log(session_ids):
    log_file = Path(AppSettings.LOG_CLEANUP_FILE)
    is_new = not log_file.exists()

    with log_file.open("a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        if is_new:
            writer.writerow(["timestamp", "session_id"])
        timestamp = datetime.now().isoformat()
        for session_id in session_ids:
            writer.writerow([timestamp, session_id])
