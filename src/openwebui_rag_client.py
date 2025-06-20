import requests
import argparse
import json
from pathlib import Path

class RAGClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.ingest_endpoint = f"{base_url}/ingest"
        self.ask_endpoint = f"{base_url}/ask"

    def upload_pdf(self, file_path: str) -> dict:
        """Upload a PDF file to the RAG system's /ingest endpoint."""
        if not Path(file_path).is_file() or not file_path.lower().endswith(".pdf"):
            raise ValueError("Invalid file path or not a PDF file")
        
        try:
            with open(file_path, "rb") as f:
                files = {"file": (Path(file_path).name, f, "application/pdf")}
                response = requests.post(self.ingest_endpoint, files=files)
                response.raise_for_status()
                return response.json()
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to upload PDF: {str(e)}") from e

    def query_pdf(self, session_id: str, query: str) -> dict:
        """Query the RAG system's /ask endpoint with a session ID and query."""
        if not session_id or not query:
            raise ValueError("Session ID and query are required")
        
        try:
            data = {"session_id": session_id, "query": query}
            response = requests.post(self.ask_endpoint, data=data)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to query PDF: {str(e)}") from e

def main():
    parser = argparse.ArgumentParser(description="RAG System Client for Open WebUI")
    parser.add_argument("--upload", type=str, help="Path to PDF file to upload")
    parser.add_argument("--session", type=str, help="Session ID for querying")
    parser.add_argument("--query", type=str, help="Query to ask about the PDF")
    args = parser.parse_args()

    client = RAGClient()

    if args.upload:
        try:
            result = client.upload_pdf(args.upload)
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"Error uploading PDF: {str(e)}")

    if args.session and args.query:
        try:
            result = client.query_pdf(args.session, args.query)
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"Error querying PDF: {str(e)}")

if __name__ == "__main__":
    main()