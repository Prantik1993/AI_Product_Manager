"""Document ingestion pipeline — loads PDFs and TXTs into ChromaDB."""

import os
import sys
from typing import Optional 

# Allow running as a script: python src/rag/ingest.py
# With pip install -e . this is not needed, but kept for convenience
if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

import chromadb
from langchain_community.document_loaders import DirectoryLoader, TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

from src.config.settings import settings
from src.monitoring.logger import get_logger

logger = get_logger("rag.ingest")


def ingest_docs(docs_dir: Optional[str] = None, clear: bool = False) -> int:
    """
    Ingest PDF and TXT documents from docs_dir into ChromaDB.

    Args:
        docs_dir: Directory to scan (defaults to settings.INTERNAL_DOCS_DIR)
        clear: If True, delete existing collection before ingesting

    Returns:
        Number of chunks ingested
    """

    docs_path = docs_dir or settings.INTERNAL_DOCS_DIR
    chroma_path = settings.VECTOR_DB_DIR

    os.makedirs(docs_path, exist_ok=True)
    os.makedirs(chroma_path, exist_ok=True)

    logger.info(f"Scanning documents in: {docs_path}")

    # Load documents
    txt_docs = DirectoryLoader(docs_path, glob="**/*.txt", loader_cls=TextLoader).load()
    pdf_docs = DirectoryLoader(docs_path, glob="**/*.pdf", loader_cls=PyPDFLoader).load()
    all_docs = txt_docs + pdf_docs

    if not all_docs:
        logger.warning("No .txt or .pdf documents found. Add files to data/internal_docs/")
        return 0

    logger.info(f"Loaded {len(pdf_docs)} PDFs and {len(txt_docs)} TXT files")

    # Split into chunks
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(all_docs)

    logger.info(f"Split into {len(chunks)} chunks")

    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=settings.OPENAI_API_KEY,
    )

    # FIX: Use PersistentClient — ChromaDB 0.6+ API
    client = chromadb.PersistentClient(path=chroma_path)

    if clear:
        try:
            client.delete_collection("company_knowledge")
            logger.info("Cleared existing collection")
        except Exception:
            pass

    # FIX: Chroma.from_documents no longer auto-persists in 0.5+
    # Using PersistentClient ensures data is written to disk automatically
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        client=client,
        collection_name="company_knowledge",
    )

    count = vector_store._collection.count()
    logger.info(f"Ingestion complete: {count} chunks stored in ChromaDB at {chroma_path}")
    return count


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Ingest documents into RAG vector database")
    parser.add_argument("--docs-dir", default=None, help="Directory with documents to ingest")
    parser.add_argument("--clear", action="store_true", help="Clear existing DB before ingesting")
    args = parser.parse_args()

    count = ingest_docs(docs_dir=args.docs_dir, clear=args.clear)
    print(f"✅ Done — {count} chunks ingested")


if __name__ == "__main__":
    main()
