import streamlit as st
import asyncio
import sys
import os
import json
import pandas as pd
from datetime import datetime

# --- 1. SETUP PATHS & ENV ---
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, "src"))

# Load Settings
try:
    from src.config.settings import settings
except Exception as e:
    st.error(f"❌ Configuration Error: {e}")
    st.stop()

# Import Enterprise Modules
from src.monitoring.logger import get_logger
from src.storage.db_manager import init_db, save_analysis, get_history
from src.graph.workflow import create_graph
from src.core.guardrails import validate_product_idea, validate_system_health

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
    try:
        init_db()
        st.session_state["db_initialized"] = True
    except Exception as e:
        st.error(f"❌ Database initialization failed: {e}")
        logger.error(f"Database init error: {e}")

# System Health Check (once per session)
if "system_healthy" not in st.session_state:
    is_healthy, health_message = validate_system_health()
    st.session_state["system_healthy"] = is_healthy
    st.session_state["health_message"] = health_message
    
    if not is_healthy:
        logger.warning(f"System health check failed: {health_message}")

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
    
    if not st.session_state.get("system_healthy", False):
        st.error("⚠️ System Issues Detected")
        with st.expander("View Details"):
            st.warning(st.session_state.get("health_message", "Unknown error"))
    else:
        st.success("✅ All Systems Operational")
    
    if settings.OPENAI_API_KEY:
        st.success("✅ OpenAI Connected")
    else:
        st.error("❌ OpenAI Key Missing")
        
    if settings.TAVILY_API_KEY:
        st.success("✅ Tavily Search Active")
    else:
        st.warning("⚠️ Search Disabled")
        
    st.markdown("---")
    st.info(f"**Environment:** {settings.ENV}\n\n**Model:** {settings.MODEL_NAME}")
    
    # Usage Guidelines
    with st.expander("📋 Usage Guidelines"):
        st.markdown("""
        **Input Requirements:**
        - Minimum 10 characters
        - Maximum 5,000 characters
        - Clear product description
        
        **Analysis Time:**
        - Typically 30-60 seconds
        - Parallel agent execution
        - Real-time web research
        """)

# --- 5. MAIN LOGIC ---
st.title(f"{settings.APP_NAME}")
st.markdown("### Enterprise Decision Support System")

# Tabs for Main Functionality
tab_new, tab_history, tab_stats = st.tabs(["🚀 New Analysis", "📜 Report History", "📊 Statistics"])

# === TAB 1: NEW ANALYSIS ===
with tab_new:
    st.markdown("### Describe Your Product Idea")
    
    user_input = st.text_area(
        "Product Feature Description:", 
        height=150, 
        placeholder="e.g. 'A subscription service for personalized coffee delivery using AI to predict taste preferences...'",
        help="Provide a detailed description of your product idea (10-5000 characters)"
    )
    
    # Character counter
    if user_input:
        char_count = len(user_input)
        word_count = len(user_input.split())
        
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.caption(f"📝 Characters: {char_count}/5000")
        with col_c2:
            st.caption(f"📄 Words: {word_count}")

    col1, col2 = st.columns([1, 4])
    with col1:
        analyze_btn = st.button("🚀 Run Analysis", type="primary", use_container_width=True)

    if analyze_btn:
        if not user_input:
            st.warning("⚠️ Please enter a product idea to analyze.")
        else:
            # === GUARDRAILS VALIDATION ===
            validation_result = validate_product_idea(user_input, user_id="streamlit_user")
            
            if not validation_result.is_valid:
                st.error(f"❌ Validation Error: {validation_result.error_message}")
                logger.warning(f"Input validation failed: {validation_result.error_message}")
            else:
                # Use sanitized input
                sanitized_input = validation_result.sanitized_input
                logger.info(f"User initiated analysis: {sanitized_input[:50]}...")
                
                # Async Runner
                async def run_analysis(idea):
                    graph = create_graph()
                    initial_state = {"user_input": idea}
                    return await graph.ainvoke(initial_state)

                with st.spinner("🤖 AI Agents are analyzing... (Market, Tech, Risk, User Feedback)"):
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    try:
                        status_text.text("Initializing agents...")
                        progress_bar.progress(10)
                        
                        # Execute Graph
                        status_text.text("Running parallel analysis...")
                        progress_bar.progress(30)
                        
                        final_state = asyncio.run(run_analysis(sanitized_input))
                        
                        progress_bar.progress(90)
                        status_text.text("Synthesizing results...")
                        
                        # Extract Data
                        verdict = final_state.get("final_verdict", {})
                        decision = verdict.get("decision", "UNKNOWN")
                        
                        progress_bar.progress(100)
                        status_text.text("Complete!")
                        
                        # Clear progress indicators
                        progress_bar.empty()
                        status_text.empty()
                        
                        # --- DISPLAY RESULTS ---
                        
                        # 1. Top Verdict Banner
                        if "GO" in str(decision).upper() and "NO" not in str(decision).upper():
                            st.markdown(f'<div class="success-box"><h2>🟢 VERDICT: {decision.upper()}</h2></div>', unsafe_allow_html=True)
                        elif "PIVOT" in str(decision).upper():
                            st.markdown(f'<div class="warning-box"><h2>🟡 VERDICT: {decision.upper()}</h2></div>', unsafe_allow_html=True)
                        elif "ERROR" in str(decision).upper():
                            st.markdown(f'<div class="fail-box"><h2>⚠️ SYSTEM ERROR</h2></div>', unsafe_allow_html=True)
                            st.error("Analysis encountered an error. Please check logs and try again.")
                        else:
                            st.markdown(f'<div class="fail-box"><h2>🔴 VERDICT: {decision.upper()}</h2></div>', unsafe_allow_html=True)
                        
                        st.divider()

                        # 2. Detailed Tabs
                        t1, t2, t3, t4, t5 = st.tabs([
                            "🏁 Executive Summary", 
                            "📊 Market Analysis", 
                            "🛠️ Technical Assessment", 
                            "⚠️ Risk Analysis", 
                            "🗣️ User Feedback"
                        ])
                        
                        with t1:
                            st.subheader("Decision Reasoning")
                            st.write(verdict.get("reasoning", "No reasoning provided."))
                            
                            if verdict.get("action_items"):
                                st.subheader("📋 Recommended Next Steps")
                                for i, item in enumerate(verdict.get("action_items", []), 1):
                                    st.markdown(f"{i}. {item}")
                            
                            confidence = verdict.get("confidence_score", 0.0)
                            st.metric("Confidence Score", f"{confidence * 100:.1f}%")
                            
                            # Display as progress bar
                            st.progress(confidence)

                        with t2:
                            st.subheader("Market Research Findings")
                            try:
                                data = json.loads(final_state.get("market_analysis", "{}"))
                                if data:
                                    st.json(data)
                                else:
                                    st.info("No market analysis data available")
                            except:
                                st.error("Error parsing market analysis data")
                            
                        with t3:
                            st.subheader("Technical Feasibility Report")
                            try:
                                data = json.loads(final_state.get("tech_analysis", "{}"))
                                if data:
                                    st.json(data)
                                else:
                                    st.info("No technical analysis data available")
                            except:
                                st.error("Error parsing technical analysis data")

                        with t4:
                            st.subheader("Risk Assessment")
                            try:
                                data = json.loads(final_state.get("risk_analysis", "{}"))
                                if data:
                                    st.json(data)
                                else:
                                    st.info("No risk analysis data available")
                            except:
                                st.error("Error parsing risk analysis data")

                        with t5:
                            st.subheader("User Sentiment Analysis")
                            try:
                                data = json.loads(final_state.get("user_feedback_analysis", "{}"))
                                if data:
                                    st.json(data)
                                else:
                                    st.info("No user feedback data available")
                            except:
                                st.error("Error parsing user feedback data")

                        # 3. Save to Database (only if not error)
                        if decision != "ERROR":
                            try:
                                save_analysis(sanitized_input, decision, final_state)
                                st.toast("✅ Analysis saved to database!", icon="💾")
                                logger.info(f"Analysis saved: {decision}")
                            except Exception as e:
                                st.warning(f"⚠️ Could not save to database: {str(e)}")
                                logger.error(f"Database save error: {e}")

                    except Exception as e:
                        progress_bar.empty()
                        status_text.empty()
                        
                        st.error(f"❌ Analysis Failed: {str(e)}")
                        logger.error(f"Analysis error: {e}", exc_info=True)
                        
                        with st.expander("🔍 Troubleshooting"):
                            st.markdown("""
                            **Common Issues:**
                            1. Check API keys in .env file
                            2. Verify internet connection for web search
                            3. Ensure RAG database is initialized
                            4. Check system logs for details
                            """)

# === TAB 2: HISTORY ===
with tab_history:
    st.subheader("Past Analysis Reports")
    
    # Filter options
    col_f1, col_f2 = st.columns([3, 1])
    with col_f1:
        search_term = st.text_input("🔍 Search reports:", placeholder="Enter keywords...")
    with col_f2:
        decision_filter = st.selectbox("Filter by decision:", ["All", "GO", "NO-GO", "PIVOT", "ERROR"])
    
    try:
        history_data = get_history()
        
        if not history_data:
            st.info("📭 No reports found in database yet. Create your first analysis!")
        else:
            # Filter data
            filtered_data = []
            for row in history_data:
                r_id, r_input, r_time, r_decision, r_report = row[0], row[1], row[2], row[3], row[4]
                
                # Apply filters
                if decision_filter != "All" and r_decision != decision_filter:
                    continue
                if search_term and search_term.lower() not in r_input.lower():
                    continue
                
                filtered_data.append(row)
            
            if not filtered_data:
                st.info("No reports match your filters.")
            else:
                st.write(f"Showing {len(filtered_data)} of {len(history_data)} reports")
                
                for row in filtered_data:
                    r_id = row[0]
                    r_input = row[1]
                    r_time = row[2]
                    r_decision = row[3]
                    
                    try:
                        r_report = json.loads(row[4])
                    except:
                        r_report = {}
                    
                    # Color code expander
                    emoji = "🔴"
                    if "GO" in str(r_decision).upper() and "NO" not in str(r_decision).upper():
                        emoji = "🟢"
                    elif "PIVOT" in str(r_decision).upper():
                        emoji = "🟡"
                    elif "ERROR" in str(r_decision).upper():
                        emoji = "⚠️"
                        
                    with st.expander(f"{emoji} {r_time[:16]} | {r_decision} | {r_input[:50]}..."):
                        st.write(f"**ID:** {r_id}")
                        st.write(f"**Full Idea:** {r_input}")
                        st.divider()
                        
                        verdict = r_report.get('final_verdict', {})
                        st.write(f"**Reasoning:** {verdict.get('reasoning', 'N/A')}")
                        
                        if verdict.get('confidence_score'):
                            st.metric("Confidence", f"{verdict.get('confidence_score') * 100:.1f}%")
                        
                        with st.expander("📋 Full Report"):
                            st.json(r_report)
                            
    except Exception as e:
        st.error(f"Error loading history: {e}")
        logger.error(f"History load error: {e}")

# === TAB 3: STATISTICS ===
with tab_stats:
    st.subheader("System Statistics")
    
    try:
        from src.storage.database import get_db_manager
        db = get_db_manager()
        stats = db.get_statistics()
        
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        
        with col_s1:
            st.metric("Total Reports", stats.get("total_reports", 0))
        
        decisions = stats.get("decisions", {})
        with col_s2:
            st.metric("GO Decisions", decisions.get("GO", 0))
        with col_s3:
            st.metric("NO-GO Decisions", decisions.get("NO-GO", 0))
        with col_s4:
            st.metric("PIVOT Decisions", decisions.get("PIVOT", 0))
        
        # Decision distribution chart
        if stats.get("total_reports", 0) > 0:
            st.subheader("Decision Distribution")
            chart_data = pd.DataFrame({
                "Decision": list(decisions.keys()),
                "Count": list(decisions.values())
            })
            st.bar_chart(chart_data.set_index("Decision"))
        
        # System info
        st.divider()
        st.subheader("System Information")
        st.write(f"**Database:** {stats.get('database_url', 'Unknown')}")
        st.write(f"**Model:** {settings.MODEL_NAME}")
        st.write(f"**Environment:** {settings.ENV}")
        
    except Exception as e:
        st.error(f"Error loading statistics: {e}")
        logger.error(f"Statistics error: {e}")