from typing import Any
from pathlib import Path
import yaml

from utils.constants import BASE_DIR

class Settings:
    def __init__(self):
        self.config_path = BASE_DIR / "config.yaml"
        self.data = self._load_config()

    def _load_config(self) -> dict:
        default_config = {
            "unsafe_mode": False,
            "allowlist": {
                "domains": [
                    r".*\.lab$", r".*\.internal$", r".*\.local$", r".*\.test$", r".*\.invalid$",
                    r"^lab-.*$", r"^test-.*$", r"^dev-.*$", r"^staging-.*$"
                ],
                "ips": ["127.0.0.1", "::1", "0.0.0.0"],
            },
            "report": {
                "company_name": "Your Lab Company Name",
                "researcher_name": "Your Name",
            },
            "targets": ["http://127.0.0.1:8080"],
            "headers": {
                "user_agent": "BugBountyPipeline/1.0 (Authorized Security Lab)",
                "custom_headers": {
                    "X-Bug-Bounty": "authorized-lab-test"
                }
            },
            "proxy": {
                "enabled": False,
                "http": "http://127.0.0.1:8082",
                "https": "http://127.0.0.1:8082"
            }
        }

        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    user_config = yaml.safe_load(f) or {}
                    # Merge user config with defaults
                    if "allowlist" in user_config:
                        default_config["allowlist"]["domains"].extend(user_config["allowlist"].get("domains", []))
                        default_config["allowlist"]["ips"].extend(user_config["allowlist"].get("ips", []))
                    
                    # Overwrite other top-level keys if present
                    for key in ["unsafe_mode", "report", "targets", "headers", "proxy"]:
                        if key in user_config:
                            if isinstance(user_config[key], dict) and isinstance(default_config[key], dict):
                                default_config[key].update(user_config[key])
                            else:
                                default_config[key] = user_config[key]

            except Exception as e:
                print(f"[SETTINGS] Error loading config.yaml: {e}")
        return default_config

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def save_allowlist(self, ip: str | None = None, domain: str | None = None):
        current_config = self.data.copy() # Start with current in-memory settings

        allowlist = current_config.setdefault("allowlist", {"ips": [], "domains": []})
        updated = False

        if ip and ip not in allowlist["ips"]:
            allowlist["ips"].append(ip)
            updated = True
        if domain and domain not in allowlist["domains"]:
            allowlist["domains"].append(domain)
            updated = True
        
        if updated:
            # Ensure the config_path is relative to BASE_DIR if it's created there
            # For saving, we should write only the parts the user modifies
            user_overrides = {}
            if self.config_path.exists():
                with open(self.config_path, "r", encoding="utf-8") as handle:
                    user_overrides = yaml.safe_load(handle) or {}

            user_overrides.setdefault("allowlist", {"ips": [], "domains": []})
            if ip and ip not in user_overrides["allowlist"]["ips"]:
                user_overrides["allowlist"]["ips"].append(ip)
            if domain and domain not in user_overrides["allowlist"]["domains"]:
                user_overrides["allowlist"]["domains"].append(domain)
            
            with open(self.config_path, "w", encoding="utf-8") as handle:
                yaml.safe_dump(user_overrides, handle, sort_keys=False)
            
            self.data = self._load_config() # Reload config to reflect changes

        return updated

# Instantiate settings globally or pass around
settings = Settings() # Instantiate and export a singleton
