# rag_system\chat\session_store.py
import logging
from sqlalchemy import create_engine, Column, String, Integer, Text
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from src.config.app_settings import AppSettings
from src.config.logging_config import setup_logging

setup_logging()

logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

engine = create_engine(AppSettings.SESSION_DB, echo=False)
Session = sessionmaker(bind=engine)

class ChatHistory(Base):
    __tablename__ = "chat_history"
    id = Column(Integer, primary_key=True)
    session_id = Column(String, nullable=False)
    session_name = Column(String, nullable=True)
    query = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    sources = Column(Text, nullable=False)

Base.metadata.create_all(engine)

def save_chat(session_id: str, query: str, response: str, sources: list, session_name: str = None):
    try:
        # If no session name is provided, use the first 50 characters of the query
        if not session_name:
            session_name = query.strip()[:50]

        with Session() as s:
            entry = ChatHistory(
                session_id=session_id,
                session_name=session_name,
                query=query,
                response=response,
                sources=", ".join(sources)
            )
            s.add(entry)
            s.commit()
            logger.info(f"Saved chat for session {session_id} with name '{session_name}'")
    except Exception as e:
        logger.exception(f"Failed to save chat for session {session_id} with name '{session_name}': {e}")
        raise RuntimeError(f"Failed to save chat for session {session_id} (name: '{session_name}'): {str(e)}")

def get_history(session_id: str):
    try:
        with Session() as s:
            records = s.query(ChatHistory).filter_by(session_id=session_id).all()
            logger.info(f"Retrieved {len(records)} history records for session {session_id}")
            return records
    except Exception as e:
        logger.exception(f"Failed to retrieve history for session {session_id}: {e}")
        raise RuntimeError(f"Failed to retrieve history: {str(e)}")
    
def get_all_history():
    try:
        with Session() as s:
            records = s.query(ChatHistory).all()
            logger.info(f"Retrieved all chat history: {len(records)} records")
            return records
    except Exception as e:
        logger.exception("Failed to retrieve all chat history")
        raise RuntimeError(f"Failed to retrieve all chat history: {str(e)}")

def delete_history(session_id: str):
    try:
        with Session() as s:
            count = s.query(ChatHistory).filter_by(session_id=session_id).delete()
            s.commit()
            logger.info(f"Deleted {count} chat records for session {session_id}")
            return count
    except Exception as e:
        logger.exception(f"Failed to delete history for session {session_id}")
        raise RuntimeError(f"Failed to delete history: {str(e)}")
