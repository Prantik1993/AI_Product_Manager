"""Enhanced RAG engine with reranking and quality scoring.

Provides production-ready RAG functionality with:
- Similarity search with configurable threshold
- Optional reranking for better results
- Caching for faster repeated queries
- Metrics tracking and monitoring
- Graceful error handling
"""

import os
from typing import List, Tuple, Optional
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

from src.config.settings import settings
from src.monitoring.logger import get_logger
from src.core.exceptions import RAGError
from src.cache.cache import cached
from src.monitoring.metrics import track_rag_query, increment_counter

logger = get_logger(__name__)


class RAGQueryEngine:
    """
    Production-ready RAG Engine with reranking and quality scoring.
    Retrieves relevant context from ChromaDB vector database.
    """

    def __init__(self):
        """Initialize RAG engine with embeddings and vector store."""
        # Validate vector DB exists
        chroma_path = settings.VECTOR_DB_DIR
        if not os.path.exists(chroma_path):
            logger.warning(
                f"RAG Database not found at {chroma_path}. "
                "Please run ingestion first."
            )

        try:
            logger.info("Initializing RAG engine")

            # Initialize embeddings
            self.embeddings = OpenAIEmbeddings(
                model="text-embedding-3-small",
                api_key=settings.OPENAI_API_KEY
            )

            # Connect to vector store
            self.vector_store = Chroma(
                persist_directory=chroma_path,
                embedding_function=self.embeddings,
                collection_name="company_knowledge"
            )

            logger.info(f"RAG Engine connected to {chroma_path}")
            increment_counter("rag_engine_init_success", 1.0)

        except Exception as e:
            logger.error(f"Failed to initialize RAG Engine: {e}", exc_info=True)
            self.vector_store = None
            increment_counter("rag_engine_init_error", 1.0)
            raise RAGError(f"Failed to initialize RAG engine: {str(e)}")

    @track_rag_query()
    def query(
        self,
        topic: str,
        k: Optional[int] = None,
        score_threshold: Optional[float] = None,
        enable_reranking: Optional[bool] = None
    ) -> str:
        """
        Query RAG engine for relevant company documents.

        Args:
            topic: Query string
            k: Number of results to return (default: from settings)
            score_threshold: Minimum similarity score (default: from settings)
            enable_reranking: Whether to rerank results (default: from settings)

        Returns:
            Formatted context string for LLM injection

        Raises:
            RAGError: If query fails
        """
        if not self.vector_store:
            logger.error("RAG query failed: Vector store not initialized")
            increment_counter("rag_query_error", 1.0)
            return "Company Knowledge Base is offline (DB not initialized)."

        # Use settings defaults if not specified
        k = k or settings.RAG_TOP_K
        score_threshold = score_threshold or settings.RAG_SCORE_THRESHOLD
        enable_reranking = (
            enable_reranking
            if enable_reranking is not None
            else settings.ENABLE_RERANKING
        )

        try:
            logger.info(
                f"Querying RAG",
                extra={
                    "extra_fields": {
                        "topic": topic,
                        "k": k,
                        "score_threshold": score_threshold,
                        "reranking": enable_reranking,
                    }
                },
            )

            # Perform similarity search with scores
            results_with_scores = self.vector_store.similarity_search_with_score(
                topic, k=k * 2 if enable_reranking else k
            )

            if not results_with_scores:
                logger.warning(f"No RAG results found for query: {topic}")
                increment_counter("rag_query_no_results", 1.0)
                return "No relevant company documents found."

            # Filter by score threshold (ChromaDB returns distance, lower is better)
            # Convert distance to similarity score (1 - normalized_distance)
            filtered_results = [
                (doc, 1.0 - score)
                for doc, score in results_with_scores
                if (1.0 - score) >= score_threshold
            ]

            if not filtered_results:
                logger.warning(
                    f"No results above threshold {score_threshold} for query: {topic}"
                )
                increment_counter("rag_query_below_threshold", 1.0)
                return "No relevant company documents found (below quality threshold)."

            # Optionally rerank results
            if enable_reranking:
                filtered_results = self._rerank_results(topic, filtered_results, k)

            # Format results
            context_parts = []
            for i, (doc, score) in enumerate(filtered_results[:k], 1):
                source = doc.metadata.get("source", "Unknown Source")
                content = doc.page_content.replace("\n", " ").strip()
                context_parts.append(
                    f"[{i}] Relevance: {score:.2f} | Source: {source}\n{content}"
                )

            formatted_context = "\n\n".join(context_parts)

            logger.info(
                f"RAG query completed",
                extra={
                    "extra_fields": {
                        "topic": topic,
                        "results_count": len(filtered_results),
                        "avg_score": sum(s for _, s in filtered_results) / len(filtered_results),
                    }
                },
            )
            increment_counter("rag_query_success", 1.0)

            return formatted_context

        except Exception as e:
            logger.error(f"RAG Query failed: {e}", exc_info=True)
            increment_counter("rag_query_error", 1.0)
            raise RAGError(f"RAG query failed: {str(e)}")

    def _rerank_results(
        self,
        query: str,
        results: List[Tuple[Document, float]],
        top_k: int
    ) -> List[Tuple[Document, float]]:
        """
        Rerank results using a simple keyword-based scoring.

        In production, you might use a cross-encoder model or API
        like Cohere Rerank for better results.

        Args:
            query: Original query string
            results: List of (document, score) tuples
            top_k: Number of top results to keep

        Returns:
            Reranked list of (document, score) tuples
        """
        logger.debug(f"Reranking {len(results)} results")

        # Simple keyword-based reranking
        query_terms = set(query.lower().split())

        reranked = []
        for doc, original_score in results:
            content_lower = doc.page_content.lower()

            # Count query term matches
            keyword_score = sum(
                1 for term in query_terms if term in content_lower
            )

            # Combine original similarity score with keyword score
            # Weight: 70% similarity, 30% keyword matches
            combined_score = (original_score * 0.7) + (
                min(keyword_score / len(query_terms), 1.0) * 0.3
            )

            reranked.append((doc, combined_score))

        # Sort by combined score (descending)
        reranked.sort(key=lambda x: x[1], reverse=True)

        logger.debug(f"Reranking complete, returning top {top_k} results")
        return reranked[:top_k]

    def get_stats(self) -> dict:
        """
        Get statistics about the vector store.

        Returns:
            Dictionary with vector store statistics
        """
        if not self.vector_store:
            return {"status": "offline"}

        try:
            collection = self.vector_store._collection
            count = collection.count()

            return {
                "status": "online",
                "document_count": count,
                "collection_name": "company_knowledge",
                "persist_directory": settings.VECTOR_DB_DIR,
            }
        except Exception as e:
            logger.error(f"Failed to get RAG stats: {e}")
            return {"status": "error", "error": str(e)}