#!/usr/bin/env python3
# Custom-built XSS Scanner (LAB ONLY)
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


class CustomXSSScanner:
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
        # Non-malicious lab-only test payloads
        self.test_payloads = self._load_payloads(BASE_DIR / "Bug Bounty" / "Kali_Pipeline" / "wordlists" / "SecLists" / "Fuzzing" / "XSS" / "robot-friendly" / "XSS-Jhaddix.txt")

    def _load_payloads(self, filepath: Path) -> List[str]:
        if not filepath.exists():
            print(f"[XSS] Warning: Payload file not found: {filepath}")
            return []
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            payloads = [line.strip() for line in f if line.strip()]
        print(f"[XSS] Loaded {len(payloads)} XSS payloads from {filepath}")
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
            print(f"[XSS] No query parameters to test on {url}")
            return findings

        for param in params:
            print(f"[XSS] Testing parameter: {param} on {url}")
            for payload in self.test_payloads:
                if pipeline_stop_requested():
                    print("[XSS] Scan stopped by user request.")
                    return findings

                test_url = self.build_test_url(url, param, payload)
                try:
                    response = self.session.get(test_url, timeout=5, verify=False)
                    if payload in response.text:
                        finding = {
                            "vuln_type": "XSS (Reflected)",
                            "severity": "HIGH",
                            "url": test_url,
                            "parameter": param,
                            "payload": payload,
                            "description": "Reflected XSS detected: payload appears in response",
                        }
                        findings.append(finding)
                        print(f"[XSS][FOUND] Reflected XSS in {param}: {payload}")
                        break  # No need to test further payloads on this param
                except Exception as e:
                    print(f"[XSS] Error testing {url}: {e}")
        return findings

    def run(self, urls: List[str]) -> List[Dict[str, Any]]:
        print(f"[XSS] Starting custom XSS scan on {len(urls)} URL(s)...")
        all_findings = []
        for url in urls:
            try:
                all_findings.extend(self.scan_url(url))
            except Exception as e:
                print(f"[XSS] Failed to scan {url}: {e}")
        self.findings.extend(all_findings)
        return all_findings


if __name__ == "__main__":
    if len(sys.argv) > 1:
        target = sys.argv[1]
        scanner = CustomXSSScanner(target)
        findings = scanner.run([target])
        print(f"[XSS] Scan complete! Found {len(findings)} findings!")
        for f in findings:
            print(f"[XSS] {f}")
