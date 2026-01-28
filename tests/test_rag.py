"""Tests for RAG functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from langchain_core.documents import Document


def test_rag_evaluation():
    """Test RAG evaluation functionality."""
    from src.rag.evaluation import RAGEvaluator
    from unittest.mock import MagicMock

    # Mock RAG engine
    mock_rag = MagicMock()
    mock_rag.query.return_value = (
        "Our budget cap is $50k. We avoid hardware and crypto products."
    )

    evaluator = RAGEvaluator(mock_rag)

    # Test evaluation
    result = evaluator.evaluate_retrieval(
        query="What is our budget?",
        expected_contains=["$50k", "budget"],
        min_score=0.5
    )

    assert result.passed is True
    assert result.score >= 0.5


def test_rag_evaluation_batch():
    """Test batch RAG evaluation."""
    from src.rag.evaluation import RAGEvaluator
    from unittest.mock import MagicMock

    mock_rag = MagicMock()
    mock_rag.query.return_value = "Test response"

    evaluator = RAGEvaluator(mock_rag)

    test_cases = [
        ("query1", ["term1"]),
        ("query2", ["term2"]),
    ]

    results = evaluator.evaluate_batch(test_cases, min_score=0.0)
    assert len(results) == 2


def test_rag_evaluation_report():
    """Test evaluation report generation."""
    from src.rag.evaluation import RAGEvaluator, RAGEvaluation
    from unittest.mock import MagicMock

    mock_rag = MagicMock()
    evaluator = RAGEvaluator(mock_rag)

    # Create mock results
    results = [
        RAGEvaluation(
            query="test",
            retrieved_docs=["doc"],
            expected_contains=["term"],
            score=0.8,
            passed=True,
            details="OK"
        )
    ]

    report = evaluator.generate_report(results)

    assert report["total_tests"] == 1
    assert report["passed"] == 1
    assert report["pass_rate"] == 1.0
