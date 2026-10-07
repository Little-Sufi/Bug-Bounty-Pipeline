import os
import subprocess
import sys
import streamlit as st
from pathlib import Path

from utils.constants import BASE_DIR, LAB_LOG_FILE
from utils.state_manager import ui_log, refresh_runtime_state, close_lab_log_handle

def start_test_lab():
    refresh_runtime_state()
    if st.session_state.pipeline_state["lab_running"]:
        ui_log("Test lab is already running.")
        return

    lab_script = BASE_DIR / "test_lab" / "test_lab_server.py"
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    lab_log_handle = open(LAB_LOG_FILE, "a", encoding="utf-8")
    process = subprocess.Popen(
        [sys.executable, "-B", str(lab_script)],
        cwd=str(BASE_DIR),
        stdout=lab_log_handle,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
    )
    st.session_state.pipeline_state["lab_process"] = process
    st.session_state.pipeline_state["lab_log_handle"] = lab_log_handle
    st.session_state.pipeline_state["lab_running"] = True
    ui_log("Starting built-in test lab on http://127.0.0.1:8080")


def stop_test_lab():
    refresh_runtime_state()
    process = st.session_state.pipeline_state.get("lab_process")
    if not process:
        ui_log("Test lab is not running.")
        return

    try:
        process.terminate()
        process.wait(timeout=5)
    except Exception:
        try:
            process.kill()
        except Exception:
            pass
    finally:
        st.session_state.pipeline_state["lab_process"] = None
        st.session_state.pipeline_state["lab_running"] = False
        close_lab_log_handle()
        ui_log("Test lab server stopped.")
