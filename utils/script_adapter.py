
#!/usr/bin/env python3
# Script Adapter - Auto-adapts scripts to target requirements and rules
# WARNING: LAB-ONLY AND AUTHORIZED USE ONLY!
import os
import yaml
import re
import shutil
from typing import Dict, Any

class ScriptAdapter:
    def __init__(self, rules_file: str = "../rules.yaml", config_file: str = "../config.yaml"):
        self.rules = self.load_yaml(rules_file)
        self.config = self.load_yaml(config_file)
        self.script_backup_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.script_backups"))
        os.makedirs(self.script_backup_dir, exist_ok=True)

    def load_yaml(self, file_path: str) -> Dict[str, Any]:
        abs_path = os.path.abspath(os.path.join(os.path.dirname(__file__), file_path))
        if os.path.exists(abs_path):
            with open(abs_path, "r") as f:
                return yaml.safe_load(f)
        return {}

    def get_target_rules(self, target_domain: str) -> Dict[str, Any]:
        """Get rules specific to a target domain"""
        target_rules = self.rules.get("general", {}).copy()
        for target in self.rules.get("targets", []):
            if target.get("domain") == target_domain:
                target_rules.update(target)
        return target_rules

    def backup_script(self, script_path: str) -> str:
        """Backup original script before modification"""
        script_name = os.path.basename(script_path)
        backup_path = os.path.join(self.script_backup_dir, f"{script_name}.bak")
        if not os.path.exists(backup_path):
            shutil.copy2(script_path, backup_path)
        return backup_path

    def adapt_script(self, script_path: str, target_domain: str) -> str:
        """Adapt a script to the target's rules and requirements"""
        print(f"[*] Adapting script {os.path.basename(script_path)} for target {target_domain}...")

        # Backup original script
        self.backup_script(script_path)

        # Get target rules
        target_rules = self.get_target_rules(target_domain)

        # Read script content
        with open(script_path, "r") as f:
            content = f.read()

        # Apply adaptations
        adapted_content = content

        # 1. Update User-Agent if needed
        if "user_agent" in target_rules:
            # Look for common user-agent patterns
            ua_patterns = [
                r"User-Agent[\s]*[:=][\s]*['\"](.*?)['\"]",
                r"headers\s*=\s*\{[^}]*'User-Agent'[\s]*:[\s]*['\"](.*?)['\"]"
            ]
            for pattern in ua_patterns:
                adapted_content = re.sub(
                    pattern,
                    lambda m: m.group(0).replace(m.group(1), target_rules["user_agent"]),
                    adapted_content
                )

        # 2. Update timeout values
        if "timeout" in target_rules:
            adapted_content = re.sub(
                r"timeout\s*=\s*\d+",
                f"timeout={target_rules['timeout']}",
                adapted_content
            )

        # 2b. Update target domain in script content
        adapted_content = adapted_content.replace("lab.example.com", target_domain)
        adapted_content = adapted_content.replace("example.com", target_domain)

        # 3. Add rate limiting if missing
        if target_rules.get("respect_rate_limits", True):
            rate_limit_code = f"""
# Auto-added by Script Adapter: Rate limiting ({target_rules['max_requests_per_second']} req/s)
import time
_last_request_time = 0
def rate_limit():
    global _last_request_time
    now = time.time()
    elapsed = now - _last_request_time
    wait_time = (1 / {target_rules['max_requests_per_second']}) - elapsed
    if wait_time > 0:
        time.sleep(wait_time)
    _last_request_time = time.time()
"""
            # Insert after imports
            import_end = adapted_content.find("\n\n", 100)  # Find first blank line after imports
            if import_end != -1:
                adapted_content = adapted_content[:import_end] + rate_limit_code + adapted_content[import_end:]

        # 4. Apply per-script overrides
        script_name = os.path.basename(script_path)
        script_overrides = self.rules.get("script_overrides", {}).get(script_name, {})
        for key, value in script_overrides.items():
            # Simple find-and-replace for script-specific settings
            adapted_content = re.sub(
                rf"{key}\s*=\s*\w+",
                f"{key} = {repr(value)}",
                adapted_content
            )

        # Save adapted script
        adapted_path = script_path.replace(".py", "_adapted.py")
        with open(adapted_path, "w") as f:
            f.write(adapted_content)

        print(f"[+] Adapted script saved to {adapted_path}")
        return adapted_path

    def restore_script(self, script_path: str) -> bool:
        """Restore original script from backup"""
        script_name = os.path.basename(script_path)
        backup_path = os.path.join(self.script_backup_dir, f"{script_name}.bak")
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, script_path)
            print(f"[+] Restored original {script_name} from backup")
            return True
        return False

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python script_adapter.py <script_path> <target_domain>")
        sys.exit(1)
    adapter = ScriptAdapter()
    adapter.adapt_script(sys.argv[1], sys.argv[2])
