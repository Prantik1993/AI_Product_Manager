"""CLI entry point for headless analysis runs."""

import asyncio
import json
import os
import sys
import time

# Safety fallback — with pip install -e . this is not needed
_root = os.path.dirname(os.path.abspath(__file__))
if _root not in sys.path:
    sys.path.insert(0, _root)

from src.config.settings import settings
from src.monitoring.logger import get_logger
from src.storage.database import get_db_manager
from src.graph.workflow import create_graph
from src.core.guardrails import validate_product_idea

logger = get_logger("app.cli")


async def main():
    print(f"\n🤖 {settings.APP_NAME} — CLI Mode")
    print("=" * 50)

    # Init DB
    try:
        db = get_db_manager()
    except Exception as e:
        logger.error(f"DB init failed: {e}")
        print(f"❌ Database error: {e}")
        return

    # Get input
    print("\n📝 Enter your product idea (then press Enter):")
    user_input = input("> ").strip()

    if not user_input:
        print("❌ Input cannot be empty.")
        return

    validation = validate_product_idea(user_input)
    if not validation.is_valid:
        print(f"❌ Validation error: {validation.error_message}")
        return

    clean_input = validation.sanitized_input
    print(f"\n🚀 Starting analysis... (30–60 seconds)")
    print("Agents running: Market | Tech | Risk | User Feedback | Decision")

    graph = create_graph()
    config = {"configurable": {"thread_id": f"cli-{int(time.time())}"}}
    start = time.time()

    try:
        final_state = await graph.ainvoke({"user_input": clean_input}, config=config)
        elapsed = time.time() - start

        verdict = final_state.get("final_verdict", {})
        decision = verdict.get("decision", "UNKNOWN").upper()
        reasoning = verdict.get("reasoning", "No reasoning provided.")
        confidence = verdict.get("confidence_score", 0.0)
        action_items = verdict.get("action_items", [])
        conflicts = verdict.get("strategy_conflicts", [])

        print(f"\n{'=' * 50}")
        print(f"🏁 VERDICT: {decision}")
        print(f"{'=' * 50}")
        print(f"\n🧠 Reasoning:\n{reasoning}")

        if conflicts:
            print(f"\n🚫 Strategy Violations:")
            for c in conflicts:
                print(f"   • {c}")

        if action_items:
            print(f"\n📋 Action Items:")
            for item in action_items:
                print(f"   • {item}")

        print(f"\n📊 Confidence: {confidence * 100:.1f}%")
        print(f"⏱  Time: {elapsed:.1f}s")

        # Save report
        if decision != "ERROR":
            try:
                report_id = db.save_report(
                    user_input=clean_input,
                    decision=decision,
                    full_state=final_state,
                    execution_time=elapsed,
                )
                print(f"\n💾 Report saved (ID: {report_id})")
            except Exception as e:
                print(f"\n⚠️  Could not save report: {e}")
                logger.error(f"Save error: {e}", exc_info=True)

        logger.info("CLI analysis complete", extra={"extra_fields": {"decision": decision, "elapsed": elapsed}})

    except Exception as e:
        elapsed = time.time() - start
        logger.error(f"Analysis failed: {e}", exc_info=True)
        print(f"\n❌ Analysis failed after {elapsed:.1f}s: {e}")
        print("\nTroubleshooting:")
        print("  1. Check OPENAI_API_KEY and TAVILY_API_KEY in .env")
        print("  2. Run: python src/rag/ingest.py (if RAG not initialized)")
        print("  3. Review logs for detail")


if __name__ == "__main__":
    asyncio.run(main())
