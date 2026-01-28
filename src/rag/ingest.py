import sys
import os

# --- 1. PATH FIX (CRITICAL) ---
# This block must be BEFORE the 'from src...' imports.
# It tells Python: "The project root is 3 folders up from this file."
current_dir = os.path.dirname(os.path.abspath(__file__))      # .../src/rag
parent_dir = os.path.dirname(current_dir)                     # .../src
project_root = os.path.dirname(parent_dir)                    # .../ai-product-manager
sys.path.append(project_root)

# --- 2. IMPORTS ---
from langchain_community.document_loaders import DirectoryLoader, TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from src.config.settings import settings
from src.monitoring.logger import get_logger

logger = get_logger("rag.ingest")

def ingest_docs():
    """
    Reads .pdf and .txt files from data/internal_docs/ and saves them to ChromaDB.
    """
    docs_path = os.path.join(settings.BASE_DIR, "data", "internal_docs")
    chroma_path = os.path.join(settings.BASE_DIR, "data", "chroma_db")
    
    # Validation
    if not os.path.exists(docs_path):
        os.makedirs(docs_path)
        logger.warning(f"Created missing folder: {docs_path}")
        return

    logger.info(f"Scanning for PDF and TXT documents in {docs_path}...")

    # --- 3. LOAD DOCUMENTS ---
    # Load .txt files (Legacy support)
    txt_loader = DirectoryLoader(docs_path, glob="**/*.txt", loader_cls=TextLoader)
    txt_docs = txt_loader.load()

    # Load .pdf files (Enterprise Standard)
    pdf_loader = DirectoryLoader(docs_path, glob="**/*.pdf", loader_cls=PyPDFLoader)
    pdf_docs = pdf_loader.load()

    # Combine them
    all_docs = txt_docs + pdf_docs
    
    if not all_docs:
        logger.warning("No documents found! Please add a .pdf or .txt file to data/internal_docs/")
        return

    logger.info(f"Found {len(pdf_docs)} PDFs and {len(txt_docs)} text files.")

    # --- 4. SPLIT & SAVE ---
    # Split text into chunks
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = splitter.split_documents(all_docs)

    try:
        # Save to Vector Database
        Chroma.from_documents(
            documents=splits,
            embedding=OpenAIEmbeddings(
                model="text-embedding-3-small", 
                api_key=settings.OPENAI_API_KEY
            ),
            persist_directory=chroma_path,
            collection_name="company_knowledge"
        )
        logger.info(f"✅ Success! Ingested {len(splits)} chunks from {len(all_docs)} files.")
        
    except Exception as e:
        logger.error(f"Failed to save Vector DB: {e}")

if __name__ == "__main__":
    ingest_docs()