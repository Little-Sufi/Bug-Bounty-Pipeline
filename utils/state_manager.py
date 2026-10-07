import json
import streamlit as st
from datetime import datetime
from pathlib import Path

from utils.constants import LOG_FILE, LAB_LOG_FILE, FINDINGS_FILE, STOP_FILE

def ensure_session_state():
    if "pipeline_state" not in st.session_state:
        st.session_state.pipeline_state = {
            "running": False,
            "logs": [],
            "findings": [],
            "lab_running": False,
            "lab_process": None,
            "lab_log_handle": None,
            "pipeline_thread": None,
            "current_step": "",
        }
    if "config" not in st.session_state:
        st.session_state.config = {
            "target": "http://127.0.0.1:8080",
            "run_xss": True,
            "run_sqli": True,
            "run_traversal": True,
            "run_headers": True,
            "auto_report": True,
        }

def read_text_lines(file_path: Path) -> list[str]:
    if not file_path.exists():
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as handle:
            return [line.rstrip("\n") for line in handle]
    except Exception:
        return []

def append_log(message: str):
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_line = f"[{timestamp}] {message}"
    with open(LOG_FILE, "a", encoding="utf-8") as handle:
        handle.write(log_line + "\n")

def ui_log(message: str):
    append_log(message)

def save_findings(findings: list):
    with open(FINDINGS_FILE, "w", encoding="utf-8") as handle:
        json.dump(findings, handle, indent=2, default=str)

def load_findings() -> list:
    if not FINDINGS_FILE.exists():
        return []
    try:
        with open(FINDINGS_FILE, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception:
        return []

def close_lab_log_handle():
    handle = st.session_state.pipeline_state.get("lab_log_handle")
    if handle:
        try:
            handle.close()
        except Exception:
            pass
    st.session_state.pipeline_state["lab_log_handle"] = None

def refresh_runtime_state():
    state = st.session_state.pipeline_state
    state["logs"] = read_text_lines(LOG_FILE)
    state["findings"] = load_findings()

    lab_process = state.get("lab_process")
    if lab_process and lab_process.poll() is not None:
        state["lab_running"] = False
        close_lab_log_handle()
        if state.get("lab_process") is not None:
            ui_log(f"Test lab exited with code {lab_process.returncode}.")
        state["lab_process"] = None

    pipeline_thread = state.get("pipeline_thread")
    state["running"] = bool(pipeline_thread and pipeline_thread.is_alive())
    if not state["running"] and STOP_FILE.exists():
        try:
            STOP_FILE.unlink()
        except OSError:
            pass

def pipeline_stop_requested() -> bool:
    return STOP_FILE.exists()

def request_pipeline_stop():
    STOP_FILE.write_text("stop\n", encoding="utf-8")

def clear_pipeline_stop():
    if STOP_FILE.exists():
        STOP_FILE.unlink()
