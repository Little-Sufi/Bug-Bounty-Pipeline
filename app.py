#!/usr/bin/env python3
# Advanced Custom Bug Bounty Pipeline GUI
# STRICTLY FOR AUTHORIZED LAB USE ONLY
import sys
import os
import time
from datetime import datetime

# Add utils to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "utils")))

import streamlit as st


st.set_page_config(
    page_title="Custom Bug Bounty Pipeline",
    page_icon="🐛",
    layout="wide",
    initial_sidebar_state="expanded",
)

from utils.constants import BASE_DIR, OUTPUT_DIR, LOG_FILE, LAB_LOG_FILE, FINDINGS_FILE, STOP_FILE

# Ensure output directory exists
OUTPUT_DIR.mkdir(exist_ok=True)

# Add paths (imports are now handled by direct relative imports)

from lab_validation import is_lab_target, require_lab_target
from utils.settings import settings


try:
    import pandas as pd
except ImportError:
    pd = None

try:
    import plotly.express as px
except ImportError:
    px = None


from utils.state_manager import ensure_session_state, read_text_lines, append_log, ui_log, save_findings, load_findings, close_lab_log_handle, refresh_runtime_state, pipeline_stop_requested, request_pipeline_stop, clear_pipeline_stop


from utils.lab_manager import start_test_lab, stop_test_lab


from utils.pipeline_manager import start_pipeline, stop_pipeline
from utils.config_manager import add_to_allowlist


from utils.report_manager import render_report_downloads

ensure_session_state()
refresh_runtime_state()

config = settings.data
if config["unsafe_mode"]:
    st.warning(
        "⚠️⚠️⚠️ UNSAFE MODE IS ENABLED! ⚠️⚠️⚠️\n"
        "You are solely responsible for any damage or legal consequences.\n"
        "Only use on targets you own or have explicit written permission to test!",
        icon="🚨",
    )

with st.sidebar:
    st.header("⚙️ Configuration")
    st.subheader("🎯 Target")

    target_input = st.text_input(
        "Target URL (LAB ONLY)",
        value=st.session_state.config.get("target", "http://127.0.0.1:8080"),
        help="Must be private IP, localhost, *.lab/*.test/*.local etc., or in your allowlist.",
    )
    st.session_state.config["target"] = target_input
    ok, reason = is_lab_target(target_input)

    if ok:
        st.success(f"✅ {reason}")
    else:
        st.error(f"⚠️ {reason}")
        col_add_ip, col_add_domain = st.columns(2)
        with col_add_ip:
            new_ip = st.text_input("Add IP to allowlist", placeholder="192.168.1.100")
            if st.button("Add IP", use_container_width=True) and new_ip:
                if settings.save_allowlist(ip=new_ip):
                    st.success(f"Added {new_ip} to allowlist.")
                else:
                    st.info(f"{new_ip} is already in the allowlist.")
                st.rerun()
        with col_add_domain:
            new_domain = st.text_input("Add domain regex", placeholder=r".*\.mycompany\.local$")
            if st.button("Add Domain", use_container_width=True) and new_domain:
                if settings.save_allowlist(domain=new_domain):
                    st.success(f"Added domain pattern {new_domain}.")
                else:
                    st.info(f"{new_domain} is already in the allowlist.")
                st.rerun()

    st.divider()
    st.subheader("🧪 Test Lab")
    col_start_lab, col_stop_lab = st.columns(2)
    with col_start_lab:
        if st.button("Start Test Lab", use_container_width=True):
            start_test_lab()
            st.rerun()
    with col_stop_lab:
        if st.button("Stop Test Lab", use_container_width=True):
            stop_test_lab()
            st.rerun()

    if st.session_state.pipeline_state["lab_running"]:
        st.success("✅ Test lab running at http://127.0.0.1:8080")

    st.divider()
    st.subheader("🔍 Scan Modules")
    st.session_state.config["run_xss"] = st.checkbox(
        "Custom XSS Scanner", value=st.session_state.config["run_xss"]
    )
    st.session_state.config["run_sqli"] = st.checkbox(
        "Custom SQLi Scanner", value=st.session_state.config["run_sqli"]
    )
    st.session_state.config["run_traversal"] = st.checkbox(
        "Custom Path Traversal Scanner", value=st.session_state.config["run_traversal"]
    )
    st.session_state.config["run_headers"] = st.checkbox(
        "Custom Security Header Scanner", value=st.session_state.config["run_headers"]
    )

    st.divider()
    col_start_pipeline, col_stop_pipeline = st.columns(2)
    with col_start_pipeline:
        if st.button("▶️ Start Pipeline", type="primary", use_container_width=True):
            if ok:
                try:
                    start_pipeline()
                except Exception as exc:
                    st.error(f"Cannot start pipeline: {exc}")
                st.rerun()
            else:
                st.error("Cannot start pipeline: invalid target.")
    with col_stop_pipeline:
        if st.button("⏹️ Stop Pipeline", use_container_width=True):
            stop_pipeline()
            st.rerun()

tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "📝 Logs", "🎯 Findings", "📄 Reports"])
findings = st.session_state.pipeline_state["findings"] or load_findings()

with tab1:
    st.header("🐛 Custom Bug Bounty Pipeline Dashboard")
    col_status, col_findings, col_critical = st.columns(3)
    with col_status:
        st.metric("Status", "RUNNING" if st.session_state.pipeline_state["running"] else "READY")
    with col_findings:
        st.metric("Total Findings", len(findings))
    with col_critical:
        critical = sum(1 for finding in findings if str(finding.get("severity", "")).upper() == "CRITICAL")
        st.metric("Critical Findings", critical)

    if findings:
        if pd is None:
            st.warning("Install pandas to render the findings table.")
        else:
            st.subheader("Quick Findings Overview")
            st.dataframe(pd.DataFrame(findings), use_container_width=True)
    else:
        st.info("No findings yet. Start the pipeline or run the test lab first.")

with tab2:
    st.header("📝 Live Logs")
    pipeline_log_text = "\n".join(st.session_state.pipeline_state["logs"]) or "No pipeline logs yet."
    st.text_area("Pipeline Log Output", value=pipeline_log_text, height=320)
    st.download_button(
        "📥 Download Pipeline Logs",
        data=pipeline_log_text,
        file_name=f"pipeline_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        mime="text/plain",
    )

    st.subheader("🧪 Test Lab Logs")
    lab_log_text = "\n".join(read_text_lines(LAB_LOG_FILE)) or "No test lab logs yet."
    st.text_area("Test Lab Log Output", value=lab_log_text, height=220)

with tab3:
    st.header("🎯 Vulnerability Findings")
    if findings:
        if pd is not None:
            df = pd.DataFrame(findings)
            st.dataframe(df, use_container_width=True)

            if px is not None and "vuln_type" in df.columns and "severity" in df.columns:
                col_chart_1, col_chart_2 = st.columns(2)
                with col_chart_1:
                    fig1 = px.pie(df, names="vuln_type", title="Findings by Type")
                    st.plotly_chart(fig1, use_container_width=True)
                with col_chart_2:
                    fig2 = px.pie(df, names="severity", title="Findings by Severity")
                    st.plotly_chart(fig2, use_container_width=True)
            elif px is None:
                st.info("Install plotly to render the findings charts.")

        st.divider()
        st.subheader("Detailed Findings")
        for index, finding in enumerate(findings, start=1):
            title = finding.get("vuln_type", "Unknown")
            severity = finding.get("severity", "Unknown")
            with st.expander(f"#{index} - {title} - {severity}"):
                st.json(finding)
    else:
        st.info("No findings yet. Start the pipeline or use the test lab.")

with tab4:
    st.header("📄 Reports")
    if findings:
        render_report_downloads(findings)
    else:
        st.info("No findings to report.")

if st.session_state.pipeline_state["running"] or st.session_state.pipeline_state["lab_running"]:
    time.sleep(1)
    st.rerun()
