import os
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger("rag.engine")

class RAGQueryEngine:
    """
    Enterprise RAG Engine.
    Retrieves relevant context from the local Vector Database (ChromaDB).
    """
    def __init__(self):
        # validation: Check if DB exists before trying to load
        if not os.path.exists(settings.DB_PATH) and not os.path.exists(os.path.join(settings.BASE_DIR, "data", "chroma_db")):
             logger.warning("RAG Database not found. Please run 'src/rag/ingest.py' first.")

        try:
            # Initialize Embeddings (The "Translator" for text -> numbers)
            self.embeddings = OpenAIEmbeddings(
                model="text-embedding-3-small",
                api_key=settings.OPENAI_API_KEY
            )
            
            # Connect to Vector DB
            # We assume the DB is stored at data/chroma_db
            chroma_path = os.path.join(settings.BASE_DIR, "data", "chroma_db")
            
            self.vector_store = Chroma(
                persist_directory=chroma_path,
                embedding_function=self.embeddings,
                collection_name="company_knowledge"
            )
            logger.info(f"RAG Engine connected to {chroma_path}")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG Engine: {e}")
            self.vector_store = None

    def query(self, topic: str, k: int = 3) -> str:
        """
        Finds the top 'k' most relevant chunks from company docs.
        Returns a string suitable for injection into an LLM prompt.
        """
        if not self.vector_store:
            return "Company Knowledge Base is offline (DB not initialized)."

        try:
            logger.info(f"Querying RAG for: {topic}")
            results = self.vector_store.similarity_search(topic, k=k)
            
            if not results:
                return "No relevant company documents found."
                
            # Combine content into a formatted string with sources
            context_parts = []
            for i, doc in enumerate(results):
                source = doc.metadata.get("source", "Unknown Source")
                content = doc.page_content.replace("\n", " ")
                context_parts.append(f"[{i+1}] (Source: {source}): {content}")
                
            return "\n\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"RAG Query failed: {e}")
            return "Error retrieving company data."