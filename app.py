import streamlit as st
import asyncio
import sys
import os
import json
import pandas as pd
from datetime import datetime

# --- 1. SETUP PATHS & ENV ---
# Ensure we can import from 'src'
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, "src"))

# Load Settings (This validates your API keys immediately)
try:
    from src.config.settings import settings
except Exception as e:
    st.error(f"❌ Configuration Error: {e}")
    st.stop()

# Import Enterprise Modules
from src.utils.logger import get_logger
from src.storage.db_manager import init_db, save_analysis, get_history
from src.graph.workflow import create_graph

# Initialize Logger
logger = get_logger("app.streamlit")

# --- 2. PAGE CONFIG ---
st.set_page_config(
    page_title=f"{settings.APP_NAME}",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Database on Startup
if "db_initialized" not in st.session_state:
    init_db()
    st.session_state["db_initialized"] = True

# --- 3. CUSTOM CSS ---
st.markdown("""
    <style>
    .main { padding-top: 2rem; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; }
    .success-box { padding: 1rem; border-radius: 8px; background-color: #d4edda; border: 1px solid #c3e6cb; color: #155724; }
    .fail-box { padding: 1rem; border-radius: 8px; background-color: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }
    .warning-box { padding: 1rem; border-radius: 8px; background-color: #fff3cd; border: 1px solid #ffeeba; color: #856404; }
    .report-card { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px solid #e9ecef; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("🤖 AI Product Manager")
    st.markdown("---")
    
    # System Status Indicators
    st.subheader("System Status")
    if settings.OPENAI_API_KEY:
        st.success("✅ OpenAI Connected")
    else:
        st.error("❌ OpenAI Key Missing")
        
    if settings.TAVILY_API_KEY:
        st.success("✅ Tavily Search Active")
    else:
        st.warning("⚠️ Search Disabled")
        
    st.markdown("---")
    st.info(f"**Environment:** {settings.ENV}\n\n**Database:** Active (SQLite)")

# --- 5. MAIN LOGIC ---
st.title(f"{settings.APP_NAME}")
st.markdown("### Enterprise Decision Support System")

# Tabs for Main Functionality
tab_new, tab_history = st.tabs(["🚀 New Analysis", "📜 Report History"])

# === TAB 1: NEW ANALYSIS ===
with tab_new:
    user_input = st.text_area(
        "Describe your product feature idea:", 
        height=150, 
        placeholder="e.g. 'A subscription service for personalized coffee delivery using AI to predict taste preferences...'"
    )

    col1, col2 = st.columns([1, 4])
    with col1:
        analyze_btn = st.button("Run Analysis", type="primary")

    if analyze_btn and user_input:
        logger.info(f"User initiated analysis: {user_input[:50]}...")
        
        # Async Runner
        async def run_analysis(idea):
            graph = create_graph()
            initial_state = {"user_input": idea}
            return await graph.ainvoke(initial_state)

        with st.spinner("🤖 Agents are working... (Market, Tech, Risk, User)"):
            try:
                # Execute Graph
                final_state = asyncio.run(run_analysis(user_input))
                
                # Extract Data
                verdict = final_state.get("final_verdict", {})
                decision = verdict.get("decision", "UNKNOWN")
                
                # --- DISPLAY RESULTS ---
                
                # 1. Top Verdict Banner
                if "GO" in str(decision).upper() and "NO" not in str(decision).upper():
                    st.markdown(f'<div class="success-box"><h2>🟢 VERDICT: {decision.upper()}</h2></div>', unsafe_allow_html=True)
                elif "PIVOT" in str(decision).upper():
                    st.markdown(f'<div class="warning-box"><h2>🟡 VERDICT: {decision.upper()}</h2></div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="fail-box"><h2>🔴 VERDICT: {decision.upper()}</h2></div>', unsafe_allow_html=True)
                
                st.divider()

                # 2. Detailed Tabs
                t1, t2, t3, t4, t5 = st.tabs(["🏁 Executive Summary", "📊 Market", "🛠️ Tech", "⚠️ Risk", "🗣️ User Feedback"])
                
                with t1:
                    st.subheader("Reasoning")
                    st.write(verdict.get("reasoning", "No reasoning provided."))
                    if verdict.get("action_items"):
                        st.subheader("📋 Action Items")
                        for item in verdict.get("action_items", []):
                            st.markdown(f"- {item}")
                    st.metric("Confidence Score", f"{verdict.get('confidence_score', 0.0) * 100:.0f}%")

                with t2:
                    data = json.loads(final_state.get("market_analysis", "{}"))
                    st.json(data)
                    
                with t3:
                    data = json.loads(final_state.get("tech_analysis", "{}"))
                    st.json(data)

                with t4:
                    data = json.loads(final_state.get("risk_analysis", "{}"))
                    st.json(data)

                with t5:
                    data = json.loads(final_state.get("user_feedback_analysis", "{}"))
                    st.json(data)

                # 3. Save to Database
                save_analysis(user_input, decision, final_state)
                st.toast("✅ Analysis saved to Database!", icon="💾")

            except Exception as e:
                st.error(f"Analysis Failed: {str(e)}")
                logger.error(f"UI Error: {e}")

    elif analyze_btn and not user_input:
        st.warning("Please enter an idea to analyze.")

# === TAB 2: HISTORY ===
with tab_history:
    st.subheader("Past Analysis Reports")
    history_data = get_history()
    
    if not history_data:
        st.info("No reports found in database yet.")
    else:
        # Convert to DataFrame for easier handling if needed, or iterate directly
        for row in history_data:
            # Row structure depends on your DB query, usually: id, input, timestamp, decision, json
            # SQLite Row objects can be accessed by index or name if row_factory is set
            r_id = row[0]
            r_input = row[1]
            r_time = row[2]
            r_decision = row[3]
            r_report = json.loads(row[4])
            
            # Color code expander
            emoji = "🔴"
            if "GO" in str(r_decision).upper() and "NO" not in str(r_decision).upper():
                emoji = "🟢"
            elif "PIVOT" in str(r_decision).upper():
                emoji = "🟡"
                
            with st.expander(f"{emoji} {r_time[:16]} - {r_decision} - {r_input[:50]}..."):
                st.write(f"**Full Idea:** {r_input}")
                st.divider()
                st.write(f"**Reasoning:** {r_report.get('final_verdict', {}).get('reasoning', 'N/A')}")
                st.json(r_report)