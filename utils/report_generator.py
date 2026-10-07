
#!/usr/bin/env python3
# REPORT GENERATOR - HIGHLY ACCURATE AND DETAILED
# WARNING: LAB-ONLY USE!
import os
import yaml
import json
from datetime import datetime
from typing import List, Dict, Any

class ReportGenerator:
    def __init__(self, config_path: str = None):
        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        if not config_path:
            config_path = os.path.join(self.base_dir, "config.yaml")
        self.config = {}
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f) or {}
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def normalize_finding(self, finding: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize findings from different scanner schemas into report format."""
        if "title" in finding and "owasp_category" in finding and "evidence" in finding:
            return finding

        severity = str(finding.get("severity", "Low")).title()
        title = finding.get("title") or finding.get("vuln_type") or "Untitled Finding"
        url = finding.get("url", "N/A")
        parameter = finding.get("parameter")
        header = finding.get("header")

        evidence_parts = [f"URL: {url}"]
        if parameter:
            evidence_parts.append(f"Parameter: {parameter}")
        if header:
            evidence_parts.append(f"Header: {header}")
        if finding.get("payload"):
            evidence_parts.append(f"Payload: {finding['payload']}")
        if finding.get("actual"):
            evidence_parts.append(f"Actual: {finding['actual']}")

        verification_steps = [f"Review the scanner evidence for {title} at {url}."]
        if parameter:
            verification_steps.append(f"Repeat the request with the {parameter} input.")
        if header:
            verification_steps.append(f"Inspect the {header} response header.")

        return {
            "owasp_category": finding.get("owasp_category", "Custom Scanner Finding"),
            "title": title,
            "description": finding.get("description", "No description provided."),
            "severity": severity,
            "evidence": "\n".join(evidence_parts),
            "verification_steps": finding.get("verification_steps", verification_steps),
        }

    def load_findings(self, vuln_dir: str = None) -> List[Dict]:
        findings = []
        if not vuln_dir:
            vuln_dir = os.path.join(self.base_dir, "02-Vuln-Assessment")
            
        # Load from owasp_top10_findings.json if exists
        owasp_file = os.path.join(self.base_dir, "scripts", "owasp_top10_findings.json")
        if os.path.exists(owasp_file):
            try:
                with open(owasp_file, "r") as f:
                    owasp_findings = json.load(f)
                    findings.extend(self.normalize_finding(item) for item in owasp_findings)
            except Exception:
                pass
        custom_findings_file = os.path.join(self.base_dir, "output", "findings.json")
        if os.path.exists(custom_findings_file):
            try:
                with open(custom_findings_file, "r", encoding="utf-8") as f:
                    custom_findings = json.load(f)
                    findings.extend(self.normalize_finding(item) for item in custom_findings)
            except Exception:
                pass
        # Load other findings
        if os.path.exists(vuln_dir):
            for filename in os.listdir(vuln_dir):
                if filename.endswith(".txt") or filename.endswith(".md"):
                    try:
                        filepath = os.path.join(vuln_dir, filename)
                        with open(filepath, "r") as f:
                            findings.append(self.normalize_finding({
                                "owasp_category": "Misc",
                                "title": filename.replace(".txt", "").replace(".md", ""),
                                "description": f.read().strip(),
                                "severity": "High" if "critical" in filename.lower() or "high" in filename.lower() else
                                             "Medium" if "medium" in filename.lower() else "Low",
                                "evidence": f"File source: {filename}",
                                "verification_steps": ["Verify contents of file in vuln assessment folder"]
                            }))
                    except Exception:
                        pass
        return findings

    def generate_html(self, findings: List[Dict]) -> str:
        report_config = self.config.get("report", {})
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bug Bounty Report - {self.timestamp}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 1000px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #2c3e50; border-bottom: 2px solid #2c3e50; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        .finding {{ border: 1px solid #ddd; margin: 15px 0; padding: 15px; border-radius: 5px; }}
        .critical {{ border-left: 5px solid #e74c3c; }}
        .high {{ border-left: 5px solid #e67e22; }}
        .medium {{ border-left: 5px solid #f1c40f; }}
        .low {{ border-left: 5px solid #2ecc71; }}
        .severity {{ font-weight: bold; padding: 3px 8px; border-radius: 3px; display: inline-block; }}
        .sev-critical {{ background: #e74c3c; color: white; }}
        .sev-high {{ background: #e67e22; color: white; }}
        .sev-medium {{ background: #f1c40f; color: black; }}
        .sev-low {{ background: #2ecc71; color: white; }}
        .verification {{ background: #ecf0f1; padding: 10px; border-radius: 3px; margin-top: 10px; }}
        pre {{ white-space: pre-wrap; word-wrap: break-word; }}
        .summary {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
    </style>
</head>
<body>
    <h1>🐛 Bug Bounty Report - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</h1>
    <div class="summary">
        <p><strong>Target:</strong> {self.config.get('targets', ['Not specified'])[0]}</p>
        <p><strong>Researcher:</strong> {report_config.get('researcher_name', self.config.get('researcher_name', 'Not specified'))}</p>
        <p><strong>Total Findings:</strong> {len(findings)}</p>
    </div>
    <h2>Verified Findings</h2>
    {''.join([f'''
    <div class="finding {finding['severity'].lower()}">
        <h3>{finding['title']} <span class="severity sev-{finding['severity'].lower()}">{finding['severity'].upper()}</span></h3>
        <p><strong>OWASP Category:</strong> {finding['owasp_category']}</p>
        <p><strong>Description:</strong></p>
        <p>{finding['description']}</p>
        <p><strong>Evidence:</strong></p>
        <pre>{finding['evidence']}</pre>
        <div class="verification">
            <p><strong>Verification Steps:</strong></p>
            <ol>
                {''.join([f'<li>{step}</li>' for step in finding.get('verification_steps', [])])}
            </ol>
        </div>
    </div>
    ''' for finding in findings])}
</body>
</html>
        """
        return html

    def generate_markdown(self, findings: List[Dict]) -> str:
        report_config = self.config.get("report", {})
        md = f"# 🐛 Bug Bounty Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        md += "## Summary\n\n"
        md += f"- **Target:** {self.config.get('targets', ['Not specified'])[0]}\n"
        md += f"- **Researcher:** {report_config.get('researcher_name', self.config.get('researcher_name', 'Not specified'))}\n"
        md += f"- **Total Findings:** {len(findings)}\n\n"
        md += "## Findings\n\n"
        for finding in findings:
            md += f"### {finding['title']} ({finding['severity']})\n\n"
            md += f"**OWASP Category:** {finding['owasp_category']}\n\n"
            md += f"**Description:** {finding['description']}\n\n"
            md += f"**Evidence:**\n```\n{finding['evidence']}\n```\n\n"
            md += "**Verification Steps:**\n"
            for step in finding.get('verification_steps', []):
                md += f"1. {step}\n"
            md += "\n---\n"
        return md

    def save_report(self, findings: List[Dict], output_dir: str = None, format: str = "html"):
        if not output_dir:
            output_dir = os.path.join(self.base_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        filename = f"bug_bounty_report_{self.timestamp}.{format}"
        filepath = os.path.join(output_dir, filename)
        if format == "html":
            content = self.generate_html(findings)
        elif format == "md" or format == "markdown":
            content = self.generate_markdown(findings)
        else:
            raise ValueError(f"Unsupported format: {format}")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[+] {format.upper()} report saved to {filepath}")
        return filepath

if __name__ == "__main__":
    generator = ReportGenerator()
    findings = generator.load_findings()
    generator.save_report(findings, format="html")
    generator.save_report(findings, format="markdown")
