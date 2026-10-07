#!/usr/bin/env python3
# Custom-built SQLi Scanner (LAB ONLY)
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


class CustomSQLiScanner:
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
        self.error_payloads = self._load_payloads(BASE_DIR / "Bug Bounty" / "Kali_Pipeline" / "wordlists" / "SecLists" / "Fuzzing" / "Databases" / "SQLi" / "Generic-SQLi.txt")
        self.time_payloads = self._load_payloads(BASE_DIR / "Bug Bounty" / "Kali_Pipeline" / "wordlists" / "SecLists" / "Fuzzing" / "Databases" / "SQLi" / "quick-SQLi.txt")

    def _load_payloads(self, filepath: Path) -> List[str]:
        if not filepath.exists():
            print(f"[SQLi] Warning: Payload file not found: {filepath}")
            return []
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            payloads = [line.strip() for line in f if line.strip()]
        print(f"[SQLi] Loaded {len(payloads)} SQLi payloads from {filepath}")
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

    def scan_url_error_based(self, url: str, param: str, payload: str) -> bool:
        test_url = self.build_test_url(url, param, payload)
        try:
            response = self.session.get(test_url, timeout=10, verify=False)
            error_patterns = [
                "SQL syntax", "mysql_fetch", "ORA-", "PostgreSQL",
                "unclosed quotation mark", "syntax error",
                "Warning: mysql", "Warning: pg_",
            ]
            for pattern in error_patterns:
                if pattern.lower() in response.text.lower():
                    return True
        except Exception:
            pass
        return False

    def scan_url_time_based(self, url: str, param: str, payload: str) -> bool:
        test_url = self.build_test_url(url, param, payload)
        normal_url = self.build_test_url(url, param, "1")
        try:
            import time
            start_normal = time.time()
            self.session.get(normal_url, timeout=15, verify=False)
            time_normal = time.time() - start_normal
            start_test = time.time()
            response_test = self.session.get(test_url, timeout=15, verify=False)
            time_test = time.time() - start_test
            if time_test > time_normal + 3:  # At least 3s slower than normal
                return True
        except Exception:
            pass
        return False

    def scan_url(self, url: str) -> List[Dict[str, Any]]:
        findings = []
        params = self.extract_query_params(url)
        if not params:
            print(f"[SQLi] No query parameters to test on {url}")
            return findings
        for param in params:
            print(f"[SQLi] Testing parameter: {param} on {url}")
            # Test error-based
            for payload in self.error_payloads:
                if pipeline_stop_requested():
                    print("[SQLi] Scan stopped by user request.")
                    return findings
                if self.scan_url_error_based(url, param, payload):
                    finding = {
                        "vuln_type": "SQL Injection (Error-Based)",
                        "severity": "CRITICAL",
                        "url": url,
                        "parameter": param,
                        "payload": payload,
                        "description": "Error-based SQLi detected: error message in response",
                    }
                    findings.append(finding)
                    print(f"[SQLi][FOUND] Error-based SQLi in {param}: {payload}")
                    break
            # Test time-based
            for payload in self.time_payloads:
                if pipeline_stop_requested():
                    print("[SQLi] Scan stopped by user request.")
                    return findings
                if self.scan_url_time_based(url, param, payload):
                    finding = {
                        "vuln_type": "SQL Injection (Time-Based)",
                        "severity": "CRITICAL",
                        "url": url,
                        "parameter": param,
                        "payload": payload,
                        "description": "Time-based SQLi detected: delayed response",
                    }
                    findings.append(finding)
                    print(f"[SQLi][FOUND] Time-based SQLi in {param}: {payload}")
                    break
        return findings

    def run(self, urls: List[str]) -> List[Dict[str, Any]]:
        print(f"[SQLi] Starting custom SQLi scan on {len(urls)} URL(s)...")
        all_findings = []
        for url in urls:
            try:
                all_findings.extend(self.scan_url(url))
            except Exception as e:
                print(f"[SQLi] Failed to scan {url}: {e}")
        self.findings.extend(all_findings)
        return all_findings


if __name__ == "__main__":
    if len(sys.argv) > 1:
        target = sys.argv[1]
        scanner = CustomSQLiScanner(target)
        findings = scanner.run([target])
        print(f"[SQLi] Scan complete! Found {len(findings)} findings!")
