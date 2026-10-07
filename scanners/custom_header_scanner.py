#!/usr/bin/env python3
# Custom-built Security Header Scanner (LAB ONLY)
# STRICTLY FOR AUTHORIZED LAB USE ONLY
import re
import requests
from typing import List, Dict, Any
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))
from lab_validation import require_lab_target, pipeline_stop_requested


class CustomHeaderScanner:
    def __init__(self, target: str):
        require_lab_target(target)
        self.target = target
        self.session = requests.Session()
        from utils.settings import settings
        headers_config = settings.get("headers", {})
        user_agent = headers_config.get("user_agent", "BugBountyPipeline/1.0")
        custom_headers = headers_config.get("custom_headers", {})
        self.session.headers.update({"User-Agent": user_agent})
        if custom_headers:
            self.session.headers.update(custom_headers)
        
        proxy_config = settings.get("proxy", {})
        if proxy_config.get("enabled", False):
            self.session.proxies.update({
                "http": proxy_config.get("http", ""),
                "https": proxy_config.get("https", "")
            })
            self.session.verify = False
        self.findings: List[Dict[str, Any]] = []
        self.required_headers = {
            "X-Frame-Options": {
                "expected": ["DENY", "SAMEORIGIN"],
                "severity": "MEDIUM",
                "description": "Missing or misconfigured clickjacking protection",
            },
            "X-XSS-Protection": {
                "expected": ["1; mode=block"],
                "severity": "LOW",
                "description": "Missing or misconfigured XSS protection header",
            },
            "X-Content-Type-Options": {
                "expected": ["nosniff"],
                "severity": "LOW",
                "description": "Missing MIME type sniffing protection",
            },
            "Content-Security-Policy": {
                "severity": "MEDIUM",
                "description": "Missing Content Security Policy",
            },
            "Strict-Transport-Security": {
                "severity": "MEDIUM",
                "description": "Missing HSTS header",
            },
        }

    def scan_url(self, url: str) -> List[Dict[str, Any]]:
        findings = []
        try:
            print(f"[HEADERS] Scanning headers on {url}")
            response = self.session.get(url, timeout=10, verify=False, allow_redirects=True)
            headers_lower = {k.lower(): v for k, v in response.headers.items()}

            for header_name, config in self.required_headers.items():
                if pipeline_stop_requested():
                    print("[HEADERS] Scan stopped by user request.")
                    return findings
                header_name_lower = header_name.lower()
                if header_name_lower not in headers_lower:
                    finding = {
                        "vuln_type": "Missing Security Header",
                        "severity": config["severity"],
                        "url": url,
                        "header": header_name,
                        "description": config["description"],
                    }
                    findings.append(finding)
                    print(f"[HEADERS][FOUND] Missing header: {header_name}")
                else:
                    actual_value = headers_lower[header_name_lower]
                    if "expected" in config:
                        match = False
                        for exp in config["expected"]:
                            if exp.lower() in actual_value.lower():
                                match = True
                                break
                        if not match:
                            finding = {
                                "vuln_type": "Misconfigured Security Header",
                                "severity": config["severity"],
                                "url": url,
                                "header": header_name,
                                "actual": actual_value,
                                "expected": config["expected"],
                                "description": f"Header {header_name} has value {actual_value}; expected one of {config['expected']}",
                            }
                            findings.append(finding)
                            print(f"[HEADERS][FOUND] Misconfigured header: {header_name}")
        except Exception as e:
            print(f"[HEADERS] Error scanning {url}: {e}")
        return findings

    def run(self, urls: List[str]) -> List[Dict[str, Any]]:
        print(f"[HEADERS] Starting custom header scan on {len(urls)} URL(s)...")
        all_findings = []
        for url in urls:
            try:
                all_findings.extend(self.scan_url(url))
            except Exception as e:
                print(f"[HEADERS] Failed to scan {url}: {e}")
        self.findings.extend(all_findings)
        return all_findings


if __name__ == "__main__":
    if len(sys.argv) > 1:
        target = sys.argv[1]
        scanner = CustomHeaderScanner(target)
        findings = scanner.run([target])
        print(f"[HEADERS] Scan complete! Found {len(findings)} findings!")
