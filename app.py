import asyncio, json, time, os, sys
import streamlit as st
import nest_asyncio

nest_asyncio.apply()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config.settings import settings
from src.graph.workflow import create_graph
from src.storage.database import get_db_manager

st.set_page_config(page_title="AI Product Manager", layout="centered")
st.title("AI Product Manager")

get_db_manager()  # init db

idea = st.text_area("Product Idea", height=120)

if st.button("Analyze"):
    if not idea.strip():
        st.warning("Enter an idea.")
        st.stop()

    graph = create_graph()
    config = {"configurable": {"thread_id": f"run-{int(time.time())}"}}
    result_container = []

    with st.status("Running agents...", expanded=True) as s:

        async def run():
            async for event in graph.astream_events({"user_input": idea}, config=config, version="v2"):
                if event.get("event") == "on_chain_end" and event.get("name") == "LangGraph":
                    out = event.get("data", {}).get("output")
                    if out:
                        result_container.append(out)

        asyncio.get_event_loop().run_until_complete(run())
        s.update(label="Done", state="complete")

    if not result_container:
        st.error("No result. Check logs.")
        st.stop()

    state = result_container[0]
    verdict = state.get("final_verdict", {})
    decision = verdict.get("decision", "UNKNOWN")
    confidence = verdict.get("confidence_score", 0)

    st.divider()

    if "GO" in decision and "NO" not in decision:
        st.success(f"✅ {decision}")
    elif "PIVOT" in decision:
        st.warning(f"🔄 {decision}")
    elif "ERROR" in decision:
        st.error(f"❌ {decision}")
    else:
        st.error(f"🔴 {decision}")

    st.metric("Confidence", f"{confidence*100:.0f}%")
    st.write(verdict.get("reasoning", ""))

    with st.expander("Agent Reports"):
        for key in ["market_analysis", "tech_analysis", "risk_analysis", "user_feedback_analysis"]:
            st.subheader(key)
            raw = state.get(key)
            if raw:
                st.json(json.loads(raw) if isinstance(raw, str) else raw)

    get_db_manager().save_report(idea, decision, state)
    st.toast("Saved ✓")