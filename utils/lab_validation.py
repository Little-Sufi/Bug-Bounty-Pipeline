#!/usr/bin/env python3
# Lab-only validation module with configurable allowlist
# STRICTLY FOR AUTHORIZED LAB USE ONLY
import ipaddress
import re
from urllib.parse import urlparse

from utils.settings import settings # Import the singleton settings object


def normalize_lab_target(target: str) -> tuple[str, str]:
    """Return the original target and a normalized hostname/IP for validation."""
    original_target = target.strip()
    normalized_target = original_target

    if "://" in original_target:
        parsed = urlparse(original_target)
    else:
        # Support raw host:port values like 127.0.0.1:8080.
        parsed = urlparse(f"//{original_target}")

    hostname = parsed.hostname or parsed.netloc
    if hostname:
        normalized_target = hostname

    return original_target, normalized_target.strip("[]")


def is_lab_target(target: str) -> tuple[bool, str]:
    """Validate that a target is strictly an authorized lab target"""
    original_target, target = normalize_lab_target(target)
    if not target:
        return False, "Empty target"

    # UNSAFE MODE: Skip all validation (MANUAL ENABLE ONLY)
    if settings.get("unsafe_mode"):
        return True, (
            "⚠️⚠️⚠️ UNSAFE MODE ENABLED! ⚠️⚠️⚠️\n"
            "You are solely responsible for any damage or legal consequences\n"
            "Only use on targets you own or have explicit written permission to test!"
        )

    # 1: Check explicit IP allowlist
    if target in settings.get("allowlist", {}).get("ips", []):
        return True, f"Valid lab target: explicitly allowed IP {target}"

    # 2: Check for localhost/loopback
    localhost_patterns = [
        r"^localhost$",
        r"^127\.(\d+)\.(\d+)\.(\d+)$",
        r"^::1$",
        r"^0\.0\.0\.0$",
        r"^::ffff:127\.0\.0\.1$",
    ]
    for pattern in localhost_patterns:
        if re.fullmatch(pattern, target):
            return True, "Valid lab target: localhost/loopback"

    # 3: Check for private IP ranges
    try:
        ip = ipaddress.ip_address(target)
        if ip.is_private:
            return True, f"Valid lab target: private IP {ip}"
        if ip.is_loopback:
            return True, "Valid lab target: loopback"
        if ip.is_link_local:
            return True, f"Valid lab target: link-local IP {ip}"
        # Check if IP is in allowlist as string
        if str(ip) in settings.get("allowlist", {}).get("ips", []):
            return True, f"Valid lab target: explicitly allowed IP {str(ip)}"
        return False, f"Target is a public IP: {ip}"
    except ValueError:
        pass

    # 4: Check domain allowlist patterns
    for pattern in settings.get("allowlist", {}).get("domains", []):
        try:
            if re.fullmatch(pattern, target):
                return True, f"Valid lab target: matches domain pattern {pattern}"
        except Exception:
            continue

    # Reject everything else
    return False, (
        f"Target '{original_target}' is not in your authorized lab allowlist!\n"
        "Add it to 'config.yaml' under 'allowlist' to use it, or enable 'unsafe_mode' (NOT RECOMMENDED)."
    )


def require_lab_target(target: str) -> None:
    ok, reason = is_lab_target(target)
    if not ok:
        raise ValueError(f"LAB ONLY VALIDATION FAILED: {reason}")


def pipeline_stop_requested() -> bool:
    from utils.constants import STOP_FILE
    return STOP_FILE.exists()
