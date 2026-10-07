#!/usr/bin/env python3
# Custom-built Path Traversal Scanner (LAB ONLY)
# STRICTLY FOR AUTHORIZED LAB USE ONLY
import re
import requests
from typing import List, Dict, Any
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))
from lab_validation import require_lab_target, pipeline_stop_requested
from utils.constants import BASE_DIR


class CustomTraversalScanner:
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
        self.lfi_payloads = self._load_payloads(BASE_DIR / "Bug Bounty" / "Kali_Pipeline" / "wordlists" / "SecLists" / "Fuzzing" / "LFI" / "LFI-Jhaddix.txt")

    def _load_payloads(self, filepath: Path) -> List[str]:
        if not filepath.exists():
            print(f"[TRAVERSAL] Warning: Payload file not found: {filepath}")
            return []
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            payloads = [line.strip() for line in f if line.strip()]
        print(f"[TRAVERSAL] Loaded {len(payloads)} LFI payloads from {filepath}")
        return payloads

    def extract_query_params(self, url: str) -> Dict[str, List[str]]:
        parsed = urlparse(url)
        return parse_qs(parsed.query)

    def build_test_url(self, url: str, param: str, payload: str) -> str:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        params[param] = [payload]
        new_query = urlencode(params, doseq=True)
        return urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment,
        ))

    def scan_url(self, url: str) -> List[Dict[str, Any]]:
        findings = []
        params = self.extract_query_params(url)
        if not params:
            print(f"[TRAVERSAL] No query parameters to test on {url}")
            return findings
        for param in params:
            print(f"[TRAVERSAL] Testing parameter: {param} on {url}")
            for payload in self.lfi_payloads:
                if pipeline_stop_requested():
                    print("[TRAVERSAL] Scan stopped by user request.")
                    return findings
                test_url = self.build_test_url(url, param, payload)
                try:
                    response = self.session.get(test_url, timeout=10, verify=False)
                    lfi_indicators = [
                        "root:x:0:0:",  # /etc/passwd pattern
                        "bin:x:1:1:",
                        "daemon:x:2:2:",
                        "127.0.0.1 localhost",  # hosts file pattern
                    ]
                    for indicator in lfi_indicators:
                        if indicator in response.text:
                            finding = {
                                "vuln_type": "LFI (Local File Inclusion)",
                                "severity": "HIGH",
                                "url": test_url,
                                "parameter": param,
                                "payload": payload,
                                "description": "LFI detected: indicator pattern in response",
                            }
                            findings.append(finding)
                            print(f"[TRAVERSAL][FOUND] LFI in {param}: {payload}")
                            break
                except Exception as e:
                    print(f"[TRAVERSAL] Error testing {url}: {e}")
        return findings

    def run(self, urls: List[str]) -> List[Dict[str, Any]]:
        print(f"[TRAVERSAL] Starting custom traversal scan on {len(urls)} URL(s)...")
        all_findings = []
        for url in urls:
            try:
                all_findings.extend(self.scan_url(url))
            except Exception as e:
                print(f"[TRAVERSAL] Failed to scan {url}: {e}")
        self.findings.extend(all_findings)
        return all_findings


if __name__ == "__main__":
    if len(sys.argv) > 1:
        target = sys.argv[1]
        scanner = CustomTraversalScanner(target)
        findings = scanner.run([target])
        print(f"[TRAVERSAL] Scan complete! Found {len(findings)} findings!")
