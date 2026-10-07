import threading
import time
import streamlit as st
from typing import List, Dict, Any

from utils.constants import BASE_DIR
from utils.state_manager import append_log, save_findings, ui_log, refresh_runtime_state, pipeline_stop_requested, clear_pipeline_stop
from utils.lab_validation import require_lab_target

# Import scanner classes
from scanners.custom_header_scanner import CustomHeaderScanner
from scanners.custom_sqli_scanner import CustomSQLiScanner
from scanners.custom_traversal_scanner import CustomTraversalScanner
from scanners.custom_xss_scanner import CustomXSSScanner

def run_custom_pipeline_worker(config: dict):
    target = config["target"]
    all_findings = []
    scanner_steps = [
        ("Custom XSS Scanner", config["run_xss"], CustomXSSScanner),
        ("Custom SQLi Scanner", config["run_sqli"], CustomSQLiScanner),
        ("Custom Path Traversal Scanner", config["run_traversal"], CustomTraversalScanner),
        ("Custom Security Header Scanner", config["run_headers"], CustomHeaderScanner),
    ]

    append_log("=" * 80)
    append_log("Starting Custom Bug Bounty Pipeline")
    append_log("=" * 80)
    append_log(f"Target: {target}")

    for step_name, enabled, scanner_cls in scanner_steps:
        if not enabled:
            append_log(f"Skipping {step_name}")
            continue
        if pipeline_stop_requested():
            append_log("Pipeline stop requested by user.")
            break

        append_log("=" * 80)
        append_log(f"Running {step_name}")
        append_log("=" * 80)
        try:
            scanner = scanner_cls(target)
            findings = scanner.run([target])
            all_findings.extend(findings)
            append_log(f"{step_name} found {len(findings)} findings.")
        except Exception as exc:
            append_log(f"{step_name} failed: {exc}")

    save_findings(all_findings)
    if pipeline_stop_requested():
        append_log(f"Pipeline stopped early. Saved {len(all_findings)} findings.")
        clear_pipeline_stop()
        return

    append_log("=" * 80)
    append_log(f"Pipeline complete. Found {len(all_findings)} total findings.")
    append_log("=" * 80)


def start_pipeline():
    config = dict(st.session_state.config)
    require_lab_target(config["target"])

    refresh_runtime_state()
    thread = st.session_state.pipeline_state.get("pipeline_thread")
    if thread and thread.is_alive():
        ui_log("Pipeline is already running.")
        return

    clear_pipeline_stop()
    st.session_state.pipeline_state["running"] = True
    st.session_state.pipeline_state["current_step"] = "Starting pipeline"
    thread = threading.Thread(target=run_custom_pipeline_worker, args=(config,), daemon=True)
    st.session_state.pipeline_state["pipeline_thread"] = thread
    ui_log("Pipeline start requested.")
    thread.start()


def stop_pipeline():
    refresh_runtime_state()
    thread = st.session_state.pipeline_state.get("pipeline_thread")
    if not thread or not thread.is_alive():
        ui_log("Pipeline is not running.")
        return
    request_pipeline_stop()
    ui_log("Pipeline stop requested.")
