import asyncio
import sys
import json
import os

# --- 1. SETUP PATHS ---
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, "src"))

try:
    # --- 2. ENTERPRISE IMPORTS ---
    from src.config.settings import settings
    from src.monitoring.logger import get_logger  # FIXED: Was src.utils.logger
    from src.storage.db_manager import init_db, save_analysis
    from src.graph.workflow import create_graph
except ImportError as e:
    print(f"❌ CRITICAL IMPORT ERROR: {e}")
    print("Ensure you have created the 'src' folder structure correctly.")
    sys.exit(1)

# Initialize Structured Logger
logger = get_logger("app.cli")

async def main():
    print(f"\n🤖 {settings.APP_NAME} (CLI Mode)")
    print("=========================================")
    
    # 1. Initialize Database
    try:
        init_db()
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return

    # 2. Get User Input
    print("\n📝 Enter your product feature idea below (Press Enter to submit):")
    user_input = input("> ").strip()

    if not user_input:
        print("❌ Error: Input cannot be empty.")
        return

    logger.info(f"Starting CLI analysis for: {user_input}")
    print("\n🚀 Starting Analysis... (This may take 30-60 seconds)")

    try:
        # 3. Build & Run the Agent Graph
        graph = create_graph()
        
        # Invoke the graph with the user input
        final_state = await graph.ainvoke({"user_input": user_input})
        
        # 4. Extract Key Results
        verdict = final_state.get("final_verdict", {})
        decision = verdict.get("decision", "UNKNOWN")
        reasoning = verdict.get("reasoning", "No reasoning provided.")
        
        # 5. Display Output
        print("\n" + "="*40)
        print(f"🏁 FINAL VERDICT: {decision.upper()}")
        print("="*40)
        print(f"\n🧠 Reasoning:\n{reasoning}\n")
        
        if verdict.get("action_items"):
            print("📋 Action Items:")
            for item in verdict.get("action_items", []):
                print(f"  - {item}")
        
        # Display confidence if available
        confidence = verdict.get("confidence_score")
        if confidence is not None:
            print(f"\n📊 Confidence: {confidence * 100:.1f}%")
        
        # 6. Save to Database
        save_analysis(user_input, decision, final_state)
        print(f"\n💾 Report saved to: {settings.DB_PATH}")
        logger.info("CLI Analysis completed successfully.")

    except Exception as e:
        logger.error(f"Analysis Failed: {e}", exc_info=True)
        print(f"\n❌ Error during analysis: {str(e)}")
        print("\nTroubleshooting tips:")
        print("  1. Verify your API keys in .env file")
        print("  2. Check that all services are running")
        print("  3. Review logs for detailed error messages")

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())