import pytest
from src.rag.engine import RAGQueryEngine

# This is a "Golden Dataset" - Questions we KNOW the answer to.
TEST_CASES = [
    {
        "query": "Can we build a hardware drone?",
        "expected_concept": "software company", 
        "forbidden_concept": "drone"
    },
    {
        "query": "What is the maximum budget for an MVP?",
        "expected_concept": "$50,000",
        "forbidden_concept": "$100,000"
    }
]

def test_rag_retrieval_accuracy():
    """
    Test if the RAG engine retrieves the correct rules from your PDF/TXT.
    """
    rag = RAGQueryEngine()
    
    for case in TEST_CASES:
        # 1. Ask the Brain
        retrieved_context = rag.query(case["query"])
        
        # 2. Evaluate the "Thinking"
        # We expect it to find the rule about "software company" or "$50k"
        assert case["expected_concept"] in retrieved_context.lower(), \
            f"❌ RAG Failed! Expected '{case['expected_concept']}' in context for query: {case['query']}"
        
        print(f"✅ Query: '{case['query']}' passed retrieval check.")

if __name__ == "__main__":
    # Allow running this file directly to see results
    test_rag_retrieval_accuracy()