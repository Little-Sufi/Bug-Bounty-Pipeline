#!/usr/bin/env python3
# Built-in Lab Test Target Simulation
# STRICTLY FOR AUTHORIZED LAB USE ONLY
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import time
import sys
from pathlib import Path

if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))
from lab_validation import is_lab_target


class VulnerableLabHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        # No security headers (so header scanner finds issues)
        self.end_headers()

        # Vulnerable to XSS
        xss_payload = params.get("xss", [""])[0]
        # Vulnerable to SQLi
        sqli_payload = params.get("id", ["1"])[0]
        # Vulnerable to LFI
        lfi_payload = params.get("file", ["index.html"])[0]

        html = f"""
        <!DOCTYPE html>
        <html>
            <head>
                <title>Test Lab - Vulnerable Target</title>
            </head>
            <body>
                <h1>Test Lab - Vulnerable Target</h1>
                <p>XSS test: {xss_payload}</p>
                <p>SQLi test (ID): {sqli_payload}</p>
                <p>LFI test (file): {lfi_payload}</p>

                <!-- Simulated SQL error for test -->
                <div style="display:none;">
                    {sqli_payload}
                    {'SQL syntax error: near ' + sqli_payload if "'" in sqli_payload or '"' in sqli_payload else ''}
                </div>

                <!-- Simulated /etc/passwd content for LFI test -->
                {'root:x:0:0:root:/root:/bin/bash' if 'passwd' in lfi_payload else ''}
                {'127.0.0.1 localhost' if 'hosts' in lfi_payload else ''}

            </body>
        </html>
        """

        # Simulate SQL time-based delay
        if "sleep" in sqli_payload.lower() or "waitfor" in sqli_payload.lower():
            time.sleep(5)

        self.wfile.write(html.encode("utf-8"))

    def log_message(self, format, *args):
        print(f"[LAB] {self.address_string()} - - {format % args}")


def start_lab_server(host="127.0.0.1", port=8080):
    ok, _ = is_lab_target(f"{host}:{port}")
    if not ok:
        raise ValueError("Test lab must only run on localhost/lab IP!")
    print("=" * 80)
    print("Test Lab - Vulnerable Target Simulation")
    print("=" * 80)
    print("Running on http://127.0.0.1:8080")
    print("\nTest URLs you can try:")
    print("  XSS: http://127.0.0.1:8080/?xss=<script>alert('xss')</script>")
    print("  SQLi: http://127.0.0.1:8080/?id=' OR '1'='1")
    print("  LFI: http://127.0.0.1:8080/?file=../../etc/passwd")
    print("=" * 80)
    server_address = (host, port)
    httpd = HTTPServer(server_address, VulnerableLabHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[LAB] Stopping server...")
        httpd.server_close()


if __name__ == "__main__":
    start_lab_server()
