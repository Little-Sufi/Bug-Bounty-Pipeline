
#!/usr/bin/env python3
# AI-Powered Error Fixer (Local Pattern-Based)
# WARNING: LAB-ONLY AND AUTHORIZED USE ONLY!
import os
import re
import subprocess
import sys
import json

class AIErrorFixer:
    def __init__(self):
        self.error_patterns = [
            {
                "name": "MissingModule",
                "pattern": r"ModuleNotFoundError: No module named ['\"](\w+)['\"]",
                "fix": self.fix_missing_module
            },
            {
                "name": "PermissionDenied",
                "pattern": r"(?i)(permission denied|access denied)",
                "fix": self.fix_permission_denied
            },
            {
                "name": "MissingGo",
                "pattern": r"(?i)(go: command not found|go not found)",
                "fix": self.fix_missing_go
            },
            {
                "name": "FileNotFound",
                "pattern": r"(?i)FileNotFoundError: \[Errno 2\] No such file or directory: ['\"](.*?)['\"]",
                "fix": self.fix_file_not_found
            },
            {
                "name": "NetworkTimeout",
                "pattern": r"(?i)(timeout|connection refused|connection reset)",
                "fix": self.fix_network_timeout
            }
        ]
        self.fix_history = []

    def load_fix_history(self):
        history_file = ".fix_history.json"
        if os.path.exists(history_file):
            with open(history_file, "r") as f:
                self.fix_history = json.load(f)

    def save_fix_history(self):
        with open(".fix_history.json", "w") as f:
            json.dump(self.fix_history, f, indent=2)

    def try_fix(self, script_name: str, error_msg: str) -> bool:
        self.load_fix_history()
        print(f"[*] Attempting to auto-fix error for {script_name}...")

        for pattern_info in self.error_patterns:
            match = re.search(pattern_info["pattern"], error_msg)
            if match:
                print(f"[*] Detected error: {pattern_info['name']}")
                try:
                    fixed = pattern_info["fix"](script_name, error_msg, match)
                    if fixed:
                        from datetime import datetime
                        self.fix_history.append({
                            "script": script_name,
                            "error_type": pattern_info["name"],
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                        self.save_fix_history()
                        return True
                except Exception as e:
                    print(f"[-] Failed to apply fix: {e}")
        return False

    def fix_missing_module(self, script_name: str, error_msg: str, match) -> bool:
        module_name = match.group(1)
        print(f"[*] Installing missing module: {module_name}")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", module_name])
            print(f"[+] Successfully installed {module_name}!")
            return True
        except Exception as e:
            print(f"[-] Failed to install {module_name}: {e}")
            return False

    def fix_permission_denied(self, script_name: str, error_msg: str, match) -> bool:
        if sys.platform == "win32":
            print("[!] On Windows, try running as Administrator (not auto-fixed)")
            return False
        else:
            print("[*] Permission denied - will use sudo on next run (if applicable)")
            return True  # The main script will handle sudo if needed

    def fix_missing_go(self, script_name: str, error_msg: str, match) -> bool:
        print("[!] Go is required for Amass/Nuclei - please install it manually")
        return False

    def fix_file_not_found(self, script_name: str, error_msg: str, match) -> bool:
        file_path = match.group(1)
        print(f"[*] Checking for {file_path}...")
        # Try to create the directory if it's a directory issue
        dir_name = os.path.dirname(file_path)
        if dir_name and not os.path.exists(dir_name):
            try:
                os.makedirs(dir_name, exist_ok=True)
                print(f"[+] Created directory: {dir_name}")
                return True
            except Exception as e:
                print(f"[-] Failed to create directory: {e}")
                return False
        return False

    def fix_network_timeout(self, script_name: str, error_msg: str, match) -> bool:
        print("[*] Network issue - will retry with longer timeout on next run")
        return True

if __name__ == "__main__":
    print("AI Error Fixer - Test Mode")
    print("Enter an error message to test:")
    test_error = input("> ")
    fixer = AIErrorFixer()
    result = fixer.try_fix("test_script.py", test_error)
    print(f"Fix applied: {result}")
