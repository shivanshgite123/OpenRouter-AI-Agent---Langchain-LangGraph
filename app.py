"""
Streamlit UI - the ONLY frontend for this project.

Talks to the FastAPI backend over HTTP (never runs the LangGraph workflow
directly in-process), polling research status until completion.
"""
from __future__ import annotations

import time

import requests
import streamlit as st

from src.config.settings import get_settings

settings = get_settings()
BACKEND_URL = settings.backend_url.rstrip("/")

st.set_page_config(
    page_title="ResearchIQ · Deep Research, Automated",
    page_icon="📜",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600&display=swap');
html, body, [data-testid="stAppViewContainer"] { background: #faf7f2 !important; color: #1a1208 !important; font-family: 'DM Sans', sans-serif; }
[data-testid="stHeader"], [data-testid="stToolbar"] { display: none !important; }
footer, #MainMenu { display: none !important; visibility: hidden; }
section[data-testid="stSidebar"] { display: none; }
.hero { background: #1a1208; padding: 2.2rem 2.4rem 2rem; border-radius: 14px; margin-bottom: 1.5rem; display: flex; align-items: flex-end; justify-content: space-between; gap: 2rem; }
.hero-eyebrow { font-family: 'DM Mono', monospace; font-size: 0.62rem; letter-spacing: .18em; text-transform: uppercase; color: #c8a96e; border-left: 2px solid #c8a96e; padding-left: 8px; margin-bottom: 0.6rem; }
.hero h1 { font-family: 'Playfair Display', serif; font-size: clamp(2rem, 5vw, 3.4rem); font-weight: 900; color: #f5ede0; line-height: 1.05; margin: 0; }
.hero h1 span { color: #c8603a; }
.hero-sub { font-family: 'DM Mono', monospace; font-size: 0.72rem; color: #8a7a62; margin-top: 0.5rem; line-height: 1.7; }
.live-badge { background: #2a1e10; border: 1px solid #3a2e1e; border-radius: 8px; padding: 10px 16px; font-family: 'DM Mono', monospace; font-size: 0.65rem; color: #c8a96e; letter-spacing: .1em; white-space: nowrap; display: flex; align-items: center; gap: 8px; }
.live-dot { width: 7px; height: 7px; border-radius: 50%; background: #c8a96e; display: inline-block; animation: blink 1.8s ease-in-out infinite; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:.2} }
.metric-row { display: flex; gap: 10px; margin-bottom: 1rem; }
.metric-card { flex: 1; background: #f0ead8; border: 1px solid #e8e0d0; border-radius: 10px; padding: 12px; text-align: center; }
.metric-val { font-family: 'Playfair Display', serif; font-size: 1.6rem; font-weight: 900; color: #c8603a; line-height: 1; }
.metric-label { font-family: 'DM Mono', monospace; font-size: 0.6rem; color: #8a7a62; text-transform: uppercase; letter-spacing: .1em; margin-top: 4px; }
.report-box { background: #fff; border: 1px solid #e8e0d0; border-radius: 12px; padding: 1.8rem 2rem; line-height: 1.85; font-size: 0.92rem; color: #3a2e1e; white-space: pre-wrap; word-wrap: break-word; }
.log-line { font-family: 'DM Mono', monospace; font-size: 0.75rem; color: #3a2e1e; padding: 4px 0; border-bottom: 1px solid #eee; }
.idle-box { border: 1.5px dashed #d8ceb8; border-radius: 14px; padding: 3rem 2rem; text-align: center; margin-top: 0.5rem; }
.idle-icon { font-family: 'Playfair Display', serif; font-size: 2.4rem; color: #d8ceb8; margin-bottom: 0.75rem; }
.idle-text { font-family: 'DM Mono', monospace; font-size: 0.72rem; color: #8a7a62; line-height: 1.9; }
</style>
""", unsafe_allow_html=True)

for key in ("research_id", "result", "error", "polling"):
    if key not in st.session_state:
        st.session_state[key] = None
if "history" not in st.session_state:
    st.session_state.history = []

st.markdown(f"""
<div class="hero">
  <div class="hero-left">
    <div class="hero-eyebrow">LangChain + LangGraph · Multi-Agent</div>
    <h1>Deep Research,<br><span>Automated.</span></h1>
    <p class="hero-sub">Plan → rewrite → search → read → rerank → analyze →<br>
    reflect → (replan loop) → solve → evaluate.</p>
  </div>
  <div class="live-badge">
    <span class="live-dot"></span>
    {"MOCK MODE" if settings.effective_mock_mode else "LIVE"}
  </div>
</div>
""", unsafe_allow_html=True)

left, right = st.columns([1, 1.4], gap="large")

with left:
    question = st.text_input(
        "Research Question",
        placeholder="e.g. Compare the CAGR of the EV market in India vs China since 2020",
        key="question_input",
    )
    run_btn = st.button("▶  Start Research", use_container_width=True)

    if run_btn:
        if not question.strip():
            st.warning("Please enter a research question first.")
        else:
            try:
                resp = requests.post(f"{BACKEND_URL}/api/research", json={"question": question}, timeout=10)
                resp.raise_for_status()
                data = resp.json()
                st.session_state.research_id = data["research_id"]
                st.session_state.result = None
                st.session_state["result_final"] = False
                st.session_state.error = None
                st.session_state.history.append(question)
            except Exception as exc:
                st.session_state.error = f"Could not reach backend at {BACKEND_URL}: {exc}"

    if st.session_state.history:
        st.markdown("<br>", unsafe_allow_html=True)
        st.caption("Recent questions")
        for h in reversed(st.session_state.history[-5:]):
            st.markdown(f'<div class="log-line">↳ {h}</div>', unsafe_allow_html=True)

with right:
    if st.session_state.error:
        st.error(st.session_state.error)

    if st.session_state.research_id and not st.session_state.get("result_final"):
        status_placeholder = st.empty()
        progress_bar = st.progress(0)
        step_order = [
            "queued", "planning", "query_rewriting", "searching", "reading",
            "reranking", "researching", "reflecting", "replanning", "solving",
            "evaluating", "completed",
        ]

        final_state = None
        for _ in range(180):  # up to ~3 minutes of polling
            try:
                status_resp = requests.get(
                    f"{BACKEND_URL}/api/research/{st.session_state.research_id}/status", timeout=10
                )
                status_resp.raise_for_status()
                status_data = status_resp.json()
            except Exception as exc:
                st.session_state.error = f"Status check failed: {exc}"
                break

            step = status_data.get("current_step") or status_data.get("status", "queued")
            try:
                pct = int((step_order.index(step) + 1) / len(step_order) * 100)
            except ValueError:
                pct = 50
            progress_bar.progress(min(pct, 100))

            with status_placeholder.container():
                st.markdown(f"**Status:** `{status_data.get('status')}`  ·  **Step:** `{step}`  ·  **Replans:** {status_data.get('replan_count', 0)}")
                for line in status_data.get("agent_logs", [])[-10:]:
                    st.markdown(f'<div class="log-line">✓ {line}</div>', unsafe_allow_html=True)
                for err in status_data.get("errors", []):
                    st.markdown(f'<div class="log-line">⚠ {err}</div>', unsafe_allow_html=True)

            if status_data.get("status") in ("completed", "failed"):
                result_resp = requests.get(f"{BACKEND_URL}/api/research/{st.session_state.research_id}", timeout=10)
                result_resp.raise_for_status()
                final_state = result_resp.json()
                break

            time.sleep(1.5)

        if final_state:
            st.session_state.result = final_state
            st.session_state["result_final"] = True
            st.rerun()

    if st.session_state.get("result"):
        res = st.session_state.result
        ev = res.get("evaluation", {})

        st.markdown(f"""
        <div class="metric-row">
          <div class="metric-card"><div class="metric-val">{ev.get('overall', '—')}</div><div class="metric-label">Overall</div></div>
          <div class="metric-card"><div class="metric-val">{ev.get('completeness', '—')}</div><div class="metric-label">Completeness</div></div>
          <div class="metric-card"><div class="metric-val">{ev.get('citation_coverage', '—')}</div><div class="metric-label">Citations</div></div>
          <div class="metric-card"><div class="metric-val">{res.get('replan_count', 0)}</div><div class="metric-label">Replans</div></div>
        </div>
        """, unsafe_allow_html=True)

        tabs = st.tabs([
            "Final Report", "Research Plan", "Sources", "Evidence",
            "Calculations", "Reflection", "Agent Activity", "Evaluation",
        ])

        with tabs[0]:
            st.markdown(f'<div class="report-box">{res.get("final_answer", "No report generated.")}</div>', unsafe_allow_html=True)
            st.download_button(
                "⬇ Download Report (.txt)",
                data=res.get("final_answer", ""),
                file_name=f"report_{res.get('research_id')}.txt",
                use_container_width=True,
            )

        with tabs[1]:
            st.json({"user_question": res.get("user_question")})

        with tabs[2]:
            for s in res.get("sources", []):
                st.markdown(f"- [{s.get('title')}]({s.get('url')})")

        with tabs[3]:
            for f in res.get("findings", []):
                with st.expander(f.get("finding", "Finding")[:80]):
                    st.write(f)

        with tabs[4]:
            st.json(res.get("calculations", []))

        with tabs[5]:
            st.json(res.get("critique", {}))

        with tabs[6]:
            for line in res.get("agent_logs", []):
                st.markdown(f'<div class="log-line">✓ {line}</div>', unsafe_allow_html=True)
            for err in res.get("errors", []):
                st.markdown(f'<div class="log-line">⚠ {err}</div>', unsafe_allow_html=True)

        with tabs[7]:
            st.json(ev)

    elif not st.session_state.research_id and not st.session_state.error:
        st.markdown("""
        <div class="idle-box">
          <div class="idle-icon">📜</div>
          <p class="idle-text">Enter a research question on the left and hit <strong>Start Research</strong>.</p>
        </div>
        """, unsafe_allow_html=True)
