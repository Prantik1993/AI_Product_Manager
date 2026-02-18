"""RAG Query Engine — ChromaDB 0.6+ compatible, with proper reranking."""

import os
from typing import List, Tuple, Optional

import chromadb
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

from src.config.settings import settings
from src.monitoring.logger import get_logger
from src.core.exceptions import RAGError

logger = get_logger(__name__)


class RAGQueryEngine:
    """
    Production RAG engine using ChromaDB PersistentClient (0.6+ API).
    Retrieves relevant company strategy context for the DecisionAgent.
    """

    def __init__(self):
        chroma_path = settings.VECTOR_DB_DIR

        if not os.path.exists(chroma_path):
            logger.warning(
                f"ChromaDB not found at {chroma_path}. "
                "Run: python scripts/ingest_docs.py"
            )

        try:
            self.embeddings = OpenAIEmbeddings(
                model="text-embedding-3-small",
                api_key=settings.OPENAI_API_KEY,
            )

            # FIX: Use PersistentClient — the new ChromaDB 0.5+ / 0.6+ API
            client = chromadb.PersistentClient(path=chroma_path)

            self.vector_store = Chroma(
                client=client,
                collection_name="company_knowledge",
                embedding_function=self.embeddings,
            )
            logger.info(f"RAGQueryEngine initialized: {chroma_path}")

        except Exception as e:
            logger.error(f"RAGQueryEngine init failed: {e}", exc_info=True)
            self.vector_store = None
            raise RAGError(f"RAG initialization failed: {e}")

    def query(self, topic: str, k: Optional[int] = None) -> str:
        """
        Retrieve relevant company documents for a given topic.
        Returns formatted context string for LLM injection.
        """
        if not self.vector_store:
            return "Company Knowledge Base is offline."

        k = k or settings.RAG_TOP_K

        try:
            # Fetch 2x results for reranking headroom
            results_with_scores = self.vector_store.similarity_search_with_score(
                topic, k=k * 2
            )

            if not results_with_scores:
                logger.warning(f"No RAG results for: {topic}")
                return "No relevant company strategy documents found."

            # Convert ChromaDB distance → similarity score (lower distance = higher similarity)
            scored = [
                (doc, 1.0 - min(score, 1.0))
                for doc, score in results_with_scores
            ]

            # Filter by threshold
            filtered = [(doc, s) for doc, s in scored if s >= settings.RAG_SCORE_THRESHOLD]
            if not filtered:
                logger.warning(f"All results below threshold {settings.RAG_SCORE_THRESHOLD}")
                return "No high-confidence strategy documents found."

            # Keyword-boosted reranking
            reranked = self._rerank(topic, filtered, k)

            # Format output
            parts = []
            for i, (doc, score) in enumerate(reranked, 1):
                source = doc.metadata.get("source", "strategy doc")
                parts.append(f"[{i}] (relevance: {score:.2f}) {source}\n{doc.page_content.strip()}")

            logger.info(f"RAG returned {len(reranked)} chunks for: {topic[:60]}")
            return "\n\n".join(parts)

        except Exception as e:
            logger.error(f"RAG query failed: {e}", exc_info=True)
            raise RAGError(f"RAG query failed: {e}")

    @staticmethod
    def _rerank(query: str, results: List[Tuple[Document, float]], top_k: int) -> List[Tuple[Document, float]]:
        """
        Keyword-boosted reranking: 70% similarity score + 30% keyword match.
        For production, replace with Cohere Rerank or a cross-encoder model.
        """
        query_terms = set(query.lower().split())
        reranked = []
        for doc, sim_score in results:
            content = doc.page_content.lower()
            keyword_hits = sum(1 for t in query_terms if t in content)
            keyword_score = min(keyword_hits / max(len(query_terms), 1), 1.0)
            combined = (sim_score * 0.7) + (keyword_score * 0.3)
            reranked.append((doc, combined))
        reranked.sort(key=lambda x: x[1], reverse=True)
        return reranked[:top_k]

    def get_stats(self) -> dict:
        if not self.vector_store:
            return {"status": "offline"}
        try:
            count = self.vector_store._collection.count()
            return {
                "status": "online",
                "document_count": count,
                "collection": "company_knowledge",
                "path": settings.VECTOR_DB_DIR,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
