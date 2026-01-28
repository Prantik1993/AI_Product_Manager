#!/usr/bin/env python
"""Document ingestion script for RAG.

Ingests documents from data/internal_docs/ into ChromaDB for RAG.
Supports: PDF, TXT, MD files.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
from src.rag.ingest import main as ingest_main


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Ingest documents into RAG vector database"
    )
    parser.add_argument(
        "--docs-dir",
        default="data/internal_docs",
        help="Directory containing documents to ingest"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing vector DB before ingesting"
    )

    args = parser.parse_args()

    print(f"📚 Ingesting documents from: {args.docs_dir}")
    if args.clear:
        print("⚠️  Clearing existing vector database...")

    ingest_main()
