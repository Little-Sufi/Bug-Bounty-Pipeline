# 🐛 Ultimate Bug Bounty Pipeline & Autonomous Vulnerability Scanner

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://python.org)
[![Streamlit](https://img.shields.io/badge/GUI-Streamlit-red?logo=streamlit)](https://streamlit.io)
[![OWASP](https://img.shields.io/badge/Compliance-OWASP%20Top%2010-orange)](https://owasp.org)
[![AI Powered](https://img.shields.io/badge/AI-Ollama%20%7C%20Qwen%202.5%20Coder-purple)](https://ollama.ai)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

Created & Maintained by **[Amar Sufiyan KC (@Little-Sufi)](https://github.com/Little-Sufi)**

---

## 🎯 Executive Overview

The **Ultimate Bug Bounty Pipeline** is an enterprise-grade, multi-threaded penetration testing and attack-surface analysis framework engineered for **zero false positives** and **autonomous AI error-recovery**. 

Combining automated passive/active OSINT, targeted scanning across **30 distinct vulnerability classes**, multi-payload confirmation logic, and an integrated local LLM healing engine (powered by Ollama and Qwen 2.5 Coder), this framework transforms manual bug hunting and vulnerability assessments into a high-speed, repeatable, and self-correcting workflow.

---

## 🚀 Key Architectural Features

1. **Autonomous AI Command & Error Recovery**:
   - Integrates local LLMs via Ollama (e.g., `qwen2.5-coder`).
   - Intercepts command errors, missing dependencies, or syntax breaks during pipeline execution.
   - Autonomously diagnoses error logs, adjusts parameters/syntax, and resumes scanning without manual intervention.
2. **Strict Zero False-Positive Validation**:
   - Every identified weakness must pass multi-payload confirmation and differential response analysis before being marked as a vulnerability.
3. **Comprehensive Vulnerability Coverage (30+ Classes)**:
   - SQL Injection (Error, Boolean, Time-based, Union)
   - Cross-Site Scripting (Reflected, Stored, DOM-based)
   - Broken Object Level Authorization (BOLA / IDOR)
   - Server-Side Request Forgery (SSRF)
   - Local & Remote File Inclusion (LFI/RFI) & Directory Traversal
   - Remote Code Execution (RCE) & Command Injection
   - Insecure Deserialization, JWT Flaws, CORS Misconfigurations, and Open Redirects.
4. **Dual Interface Options**:
   - **Streamlit Web Dashboard (`app.py`)**: Real-time visual monitoring, live output logs, target configuration, and one-click report generation.
   - **Interactive CLI & Launcher (`main.py` / `run.bat`)**: High-performance headless terminal execution for headless servers or automated scripts.
5. **State Management & Fault Tolerance**:
   - Automatic session checkpointing to `.pipeline_state.json`. If a scan is halted or a machine reboots, execution resumes from the exact test state.
6. **Automated Reporting with CVSS v3.1 Scoring**:
   - Exports professional, sanitized vulnerability reports in **Markdown** and **HTML** formats ready for bug bounty platforms (HackerOne, Bugcrowd, Intigriti) or internal enterprise remediation.
7. **Built-In Local Test Lab (`test_lab/`)**:
   - Includes `test_lab_server.py`, a controlled vulnerable environment for benchmarking scanner rules and offline practice.

---

## 📁 Repository Structure

```text
Bug-Bounty-Pipeline/
├── app.py                      # Streamlit interactive web dashboard
├── main.py                     # CLI launcher and interactive console menu
├── run-full-pipeline.py        # Core multi-threaded pipeline execution engine
├── config.yaml                 # Global framework configuration & tool paths
├── rules.yaml                  # Detection rules, signatures, and payload thresholds
├── requirements.txt            # Python package dependencies
├── 00-Complete-Bug-Bounty-Guide.md # Exhaustive methodology guide for all 30 vuln classes
├── Home.md                     # Obsidian vault entry point and quick links
├── scanners/                   # Specialized scanning modules (XSS, SQLi, LFI, Headers)
├── scripts/                    # Recon engine (recon.py) and OWASP Top 10 scanner
├── utils/                      # Core helpers: State manager, report generator, AI error fixer
├── test_lab/                   # Local vulnerable test server for offline validation
└── wordlists/                  # Curated fuzzing lists, headers, and payload dictionaries
```

---

## 🛠️ Quick Start & Installation

### 1. Prerequisites
- Python 3.10 or higher
- Git
- (Optional) [Ollama](https://ollama.ai) with `qwen2.5-coder:7b` for local AI auto-correction

### 2. Setup Virtual Environment
```bash
# Clone the repository
git clone https://github.com/Little-Sufi/Bug-Bounty-Pipeline.git
cd Bug-Bounty-Pipeline

# Create and activate virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Launching the Interfaces

#### Launch Web GUI:
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501` to access the visual dashboard.

#### Launch Interactive CLI:
```bash
python main.py
# Or on Windows:
run.bat
```

---

## 📓 Obsidian Vault Integration

This repository is fully configured as an **Obsidian-compatible knowledge base**:
1. Open Obsidian -> **Open folder as vault** -> Select `Bug-Bounty-Pipeline`.
2. Start from **`Home.md`** or **`00-Complete-Bug-Bounty-Guide.md`**.
3. All internal links and tables render seamlessly with native Obsidian graph navigation.

---

## ⚖️ Legal & Ethical Disclaimer

> **WARNING:** This tool and methodology are designed **strictly for authorized penetration testing**, educational research, and legitimate bug bounty engagements with explicit written permission. Unauthorized testing against target systems without consent is illegal and unethical. The author assumes no liability for misuse.
