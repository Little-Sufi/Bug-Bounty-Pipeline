import yaml
from pathlib import Path

from utils.constants import BASE_DIR

def add_to_allowlist(ip: str | None = None, domain: str | None = None):
    config_path = BASE_DIR / "config.yaml"
    current_config = {}
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as handle:
            current_config = yaml.safe_load(handle) or {}

    allowlist = current_config.setdefault("allowlist", {"ips": [], "domains": []})
    updated = False

    if ip and ip not in allowlist["ips"]:
        allowlist["ips"].append(ip)
        updated = True
    if domain and domain not in allowlist["domains"]:
        allowlist["domains"].append(domain)
        updated = True

    if updated:
        with open(config_path, "w", encoding="utf-8") as handle:
            yaml.safe_dump(current_config, handle, sort_keys=False)

    return updated
