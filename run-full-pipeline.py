
#!/usr/bin/env python3
# FULLY ROBUST, FAST, AUTO-RESUME Bug Bounty Pipeline
# WARNING: STRICTLY FOR AUTHORIZED LAB USE ONLY!
import argparse
import subprocess
import os
import sys
# Set console encoding to UTF-8 to prevent emoji errors on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
import time
import json
import psutil
import atexit
import signal
from datetime import datetime
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add utils to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "utils")))
from ai_error_fixer import AIErrorFixer
from lab_validation import require_lab_target
from script_adapter import ScriptAdapter

class PipelineState:
    def __init__(self, state_file: str = ".pipeline_state.json", config_file: str = "config.yaml"):
        self.state_file = state_file
        self.state = self.load()
        self.config = self.load_config(config_file)

    def load(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"completed_scripts": [], "failed_scripts": [], "findings": [], "last_update": datetime.now().isoformat()}

    def load_config(self, config_file: str) -> Dict[str, Any]:
        try:
            import yaml
            if os.path.exists(config_file):
                with open(config_file, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f)
        except Exception:
            pass
        return {}

    def save(self):
        self.state["last_update"] = datetime.now().isoformat()
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2)

    def mark_completed(self, script: str):
        if script not in self.state["completed_scripts"]:
            self.state["completed_scripts"].append(script)
        self.state["failed_scripts"] = [f for f in self.state["failed_scripts"] if f.get("script") != script]
        self.save()

    def mark_failed(self, script: str, error: str):
        # Don't mark as failed if already completed
        if script in self.state["completed_scripts"]:
            return
        # Check if already in failed list
        if not any(f.get("script") == script for f in self.state["failed_scripts"]):
            self.state["failed_scripts"].append({"script": script, "error": error, "timestamp": datetime.now().isoformat(), "retry_count": 0})
        else:
            for f in self.state["failed_scripts"]:
                if f.get("script") == script:
                    f["retry_count"] = f.get("retry_count", 0) + 1
                    f["last_error"] = error
                    f["timestamp"] = datetime.now().isoformat()
        self.save()

# Global state object
STATE: PipelineState = None

def monitor_resources():
    """Monitor resources - NON-BLOCKING, no delays!"""
    try:
        cpu_percent = psutil.cpu_percent(interval=None)
        memory_percent = psutil.virtual_memory().percent
        return cpu_percent > 90 or memory_percent > 95
    except Exception:
        return False

def save_state_on_exit():
    """Auto-save state on ANY exit (normal or abnormal)"""
    if STATE:
        STATE.save()
        print(f"\n[*] State auto-saved to {STATE.state_file}")

def run_single_script(script: str, script_dir: str, script_adapter: ScriptAdapter, error_fixer: AIErrorFixer, primary_target: str) -> bool:
    """Run a single script, return True if success"""
    original_script_path = os.path.abspath(os.path.join(script_dir, script))
    if not os.path.exists(original_script_path):
        print(f"[-] Script not found: {original_script_path}")
        return False
    script_to_run = original_script_path
    try:
        # Adapt script
        script_to_run = script_adapter.adapt_script(original_script_path, primary_target)
    except Exception:
        script_to_run = original_script_path

    max_retries = 5
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    root_dir = os.path.dirname(os.path.abspath(__file__))
    env["PYTHONPATH"] = root_dir + os.pathsep + env.get("PYTHONPATH", "")
    for retry in range(max_retries):
        # Quick resource check
        if monitor_resources():
            print("[!] High resource usage detected; pausing briefly before retrying...")
            time.sleep(1)

        try:
            command = [sys.executable, "-B", script_to_run]
            if os.path.basename(script).startswith("owasp_top10_scanner"):
                command.append(primary_target)
            result = subprocess.run(
                command,
                cwd=script_dir,
                check=True,
                capture_output=True,
                encoding='utf-8',
                errors='replace',
                timeout=300,
                env=env,
            )
            if result.stdout.strip():
                print(result.stdout.strip()[-800:])
            print(f"[+] {script} completed successfully!")
            return True
        except subprocess.TimeoutExpired:
            print(f"[-] {script} timed out (try {retry+1}/{max_retries})")
        except subprocess.CalledProcessError as e:
            error_msg = (e.stderr or e.stdout or str(e)).strip()
            print(f"[-] {script} failed (try {retry+1}/{max_retries}): {error_msg[:200]}")
            if script_to_run != original_script_path:
                print(f"[*] Retrying {script} with original script instead of adapted copy...")
                script_to_run = original_script_path
                continue
            # Try to fix
            if retry < max_retries - 1:
                try:
                    if error_fixer.try_fix(script, error_msg):
                        print(f"[+] Auto-fixed, retrying {script}")
                        continue
                except Exception:
                    pass
        except Exception as e:
            print(f"[-] Unexpected error running {script} (try {retry+1}/{max_retries}): {str(e)}")
    return False

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the bug bounty pipeline.")
    parser.add_argument(
        "--resume",
        choices=["ask", "auto", "yes", "no"],
        default="ask",
        help="How to handle an existing pipeline state file.",
    )
    return parser.parse_args()


def should_resume(existing_state: bool, resume_mode: str, state_file: str) -> bool:
    if not existing_state:
        return False
    if resume_mode == "yes":
        return True
    if resume_mode == "no":
        return False
    if resume_mode == "auto":
        return not sys.stdin.isatty()

    while True:
        resume = input("\nResume previous run? (Y/n): ").strip().lower()
        if resume in ["", "y", "yes"]:
            return True
        if resume in ["n", "no"]:
            return False
        print("[!] Please answer y or n.")


def main():
    global STATE
    args = parse_args()
    print("=" * 80)
    print("ULTIMATE BUG BOUNTY PIPELINE - 100% FAILURE-RESISTANT")
    print("=" * 80)
    print("\nWARNING: FOR AUTHORIZED LAB USE ONLY!\n")

    # Initialize state
    state_file = ".pipeline_state.json"
    STATE = PipelineState(state_file=state_file)

    # Register exit handlers
    atexit.register(save_state_on_exit)
    signal.signal(signal.SIGTERM, lambda s, f: sys.exit(0))
    signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))

    # Check if state exists and ask to resume
    existing_state = bool(STATE.state["completed_scripts"] or STATE.state["failed_scripts"])
    if existing_state:
        print(f"\n[*] Found previous state!")
        print(f"   - Completed scripts: {len(STATE.state['completed_scripts'])}")
        print(f"   - Failed scripts: {len(STATE.state['failed_scripts'])}")
        if should_resume(existing_state, args.resume, state_file):
            print("[*] Resuming...")
        else:
            backup_file = f".pipeline_state_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            os.rename(state_file, backup_file)
            print(f"[*] Old state backed up to {backup_file}")
            STATE = PipelineState(state_file=state_file)

    # Initialize adapters
    error_fixer = AIErrorFixer()
    script_adapter = ScriptAdapter()

    # Get target
    primary_target = STATE.config.get("targets", ["lab.example.com"])[0] if STATE.config else "lab.example.com"
    require_lab_target(primary_target)

    # Script directories
    base_dir = os.path.dirname(__file__)
    script_dir = os.path.abspath(os.path.join(base_dir, "scripts"))

    # Define script order (simplified)
    all_scripts = [
        "recon.py",
        "owasp_top10_scanner.py"
    ]

    # Filter out completed scripts
    scripts_to_run = [s for s in all_scripts if s not in STATE.state["completed_scripts"]]
    if not scripts_to_run:
        print("\n[*] All scripts completed!")
    else:
        print(f"\n[*] Running {len(scripts_to_run)} scripts...")

        # Run scripts (simplified)
        groups = [
            ["recon.py"],  # Recon first
            ["owasp_top10_scanner.py"]  # OWASP Top 10 scan
        ]

        for group in groups:
            # Filter group to only scripts that need to run
            group_to_run = [s for s in group if s in scripts_to_run]
            if not group_to_run:
                continue

            print(f"\n[*] Running group of {len(group_to_run)} scripts...")
            # Parallel execution within group for MAX SPEED!
            with ThreadPoolExecutor(max_workers=min(4, len(group_to_run))) as executor:
                futures = {
                    executor.submit(
                        run_single_script,
                        script,
                        script_dir,
                        script_adapter,
                        error_fixer,
                        primary_target
                    ): script for script in group_to_run
                }

                for future in as_completed(futures):
                    script = futures[future]
                    try:
                        success = future.result()
                        if success:
                            STATE.mark_completed(script)
                        else:
                            STATE.mark_failed(script, "Max retries exceeded")
                    except Exception as e:
                        print(f"[-] Error in future for {script}: {e}")
                        STATE.mark_failed(script, str(e))
                    finally:
                        STATE.save()  # Save after every script!

    # Generate report
    print("\n" + "=" * 80)
    print("[*] Generating report...")
    print("=" * 80)
    try:
        from report_generator import ReportGenerator
        generator = ReportGenerator()
        findings = generator.load_findings()
        generator.save_report(findings, format="html")
        generator.save_report(findings, format="markdown")
        print("\n[+] Report generation complete!")
    except Exception as e:
        print(f"[-] Report generation failed: {e}")

    # Final summary
    print("\n" + "=" * 80)
    print("📊 PIPELINE SUMMARY")
    print("=" * 80)
    print(f"Total scripts: {len(all_scripts)}")
    print(f"Completed: {len(STATE.state['completed_scripts'])}")
    print(f"Failed: {len(STATE.state['failed_scripts'])}")
    if STATE.state["failed_scripts"]:
        print(f"\nFailed scripts (check {state_file} for details):")
        for f in STATE.state["failed_scripts"]:
            print(f"  - {f['script']} (tries: {f.get('retry_count', 0)+1})")
    print("\n[*] State saved - run again to resume!")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[!] UNHANDLED EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Ensure state is saved even if everything else fails
        if STATE:
            STATE.save()
