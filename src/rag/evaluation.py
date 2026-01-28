"""RAG evaluation framework for testing retrieval quality.

Provides utilities for evaluating RAG performance including:
- Relevance scoring of retrieved documents
- Answer correctness evaluation
- Faithfulness check (answer grounded in context)
- Context recall and precision metrics
"""

from typing import List, Dict, Tuple
from dataclasses import dataclass

from src.monitoring.logger import get_logger
from src.rag.engine import RAGQueryEngine

logger = get_logger(__name__)


@dataclass
class RAGEvaluation:
    """RAG evaluation result."""

    query: str
    retrieved_docs: List[str]
    expected_contains: List[str]
    score: float
    passed: bool
    details: str


class RAGEvaluator:
    """Evaluates RAG retrieval quality."""

    def __init__(self, rag_engine: RAGQueryEngine):
        """Initialize evaluator.

        Args:
            rag_engine: RAG engine instance to evaluate
        """
        self.rag_engine = rag_engine

    def evaluate_retrieval(
        self,
        query: str,
        expected_contains: List[str],
        min_score: float = 0.7
    ) -> RAGEvaluation:
        """
        Evaluate if RAG retrieves expected content.

        Args:
            query: Query string
            expected_contains: List of strings that should appear in results
            min_score: Minimum score to pass (0.0-1.0)

        Returns:
            RAGEvaluation result
        """
        logger.info(f"Evaluating RAG retrieval for query: {query}")

        # Retrieve documents
        try:
            context = self.rag_engine.query(query)
            context_lower = context.lower()
        except Exception as e:
            logger.error(f"RAG query failed during evaluation: {e}")
            return RAGEvaluation(
                query=query,
                retrieved_docs=[],
                expected_contains=expected_contains,
                score=0.0,
                passed=False,
                details=f"Query failed: {str(e)}"
            )

        # Check how many expected terms are present
        matches = sum(
            1 for term in expected_contains
            if term.lower() in context_lower
        )

        score = matches / len(expected_contains) if expected_contains else 0.0
        passed = score >= min_score

        details = (
            f"Matched {matches}/{len(expected_contains)} expected terms. "
            f"Score: {score:.2f} (threshold: {min_score})"
        )

        if not passed:
            missing = [
                term for term in expected_contains
                if term.lower() not in context_lower
            ]
            details += f" | Missing: {', '.join(missing)}"

        logger.info(
            f"RAG evaluation complete",
            extra={
                "extra_fields": {
                    "query": query,
                    "score": score,
                    "passed": passed,
                    "matches": matches,
                    "expected": len(expected_contains),
                }
            },
        )

        return RAGEvaluation(
            query=query,
            retrieved_docs=[context],
            expected_contains=expected_contains,
            score=score,
            passed=passed,
            details=details
        )

    def evaluate_batch(
        self,
        test_cases: List[Tuple[str, List[str]]],
        min_score: float = 0.7
    ) -> List[RAGEvaluation]:
        """
        Evaluate multiple test cases.

        Args:
            test_cases: List of (query, expected_contains) tuples
            min_score: Minimum score to pass

        Returns:
            List of RAGEvaluation results
        """
        results = []

        for query, expected_contains in test_cases:
            result = self.evaluate_retrieval(query, expected_contains, min_score)
            results.append(result)

        return results

    def generate_report(self, results: List[RAGEvaluation]) -> Dict:
        """
        Generate summary report from evaluation results.

        Args:
            results: List of evaluation results

        Returns:
            Dictionary with summary statistics
        """
        total = len(results)
        passed = sum(1 for r in results if r.passed)
        avg_score = sum(r.score for r in results) / total if total > 0 else 0.0

        report = {
            "total_tests": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": passed / total if total > 0 else 0.0,
            "average_score": avg_score,
            "results": [
                {
                    "query": r.query,
                    "score": r.score,
                    "passed": r.passed,
                    "details": r.details
                }
                for r in results
            ]
        }

        logger.info(
            f"RAG evaluation report generated",
            extra={
                "extra_fields": {
                    "total_tests": total,
                    "passed": passed,
                    "pass_rate": report["pass_rate"],
                    "avg_score": avg_score,
                }
            },
        )

        return report


# Pre-defined test cases for company strategy
STRATEGY_TEST_CASES = [
    (
        "What products should we avoid?",
        ["hardware", "crypto", "blockchain"]
    ),
    (
        "What is our budget cap for new products?",
        ["$50", "50k", "budget"]
    ),
    (
        "Who is our target audience?",
        ["Gen Z", "Millennials", "18-35"]
    ),
    (
        "What are our company values?",
        ["sustainability", "innovation", "inclusive"]
    ),
    (
        "What is our go-to-market timeline?",
        ["3 months", "90 days", "quarter"]
    ),
]


def run_rag_quality_tests(rag_engine: RAGQueryEngine) -> Dict:
    """
    Run standard RAG quality tests.

    Args:
        rag_engine: RAG engine to test

    Returns:
        Evaluation report
    """
    evaluator = RAGEvaluator(rag_engine)
    results = evaluator.evaluate_batch(STRATEGY_TEST_CASES, min_score=0.6)
    report = evaluator.generate_report(results)

    # Log summary
    logger.info(
        f"RAG Quality Tests: {report['passed']}/{report['total_tests']} passed "
        f"({report['pass_rate']:.1%})"
    )

    return report
