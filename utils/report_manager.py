import streamlit as st
from datetime import datetime
from typing import List

def render_report_downloads(findings: List[dict]):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    html_report = f"""
    <html>
        <head>
            <title>Bug Bounty Report - {timestamp}</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }}
                h1 {{ color: #e74c3c; }}
                .finding {{ border: 1px solid #ddd; border-radius: 8px; padding: 16px; margin: 12px 0; }}
                .critical {{ border-left: 8px solid #e74c3c; }}
                .high {{ border-left: 8px solid #e67e22; }}
                .medium {{ border-left: 8px solid #f1c40f; }}
                .low {{ border-left: 8px solid #2ecc71; }}
            </style>
        </head>
        <body>
            <h1>Bug Bounty Report</h1>
            <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>Total findings: {len(findings)}</p>
            <hr>
    """
    for finding in findings:
        sev_class = finding.get("severity", "low").lower()
        html_report += f"""
            <div class="finding {sev_class}">
                <h3>{finding.get('vuln_type', 'Unknown')} - {finding.get('severity', 'Unknown')}</h3>
                <p>URL: {finding.get('url', 'N/A')}</p>
                <p>Description: {finding.get('description', 'N/A')}</p>
            </div>
        """
    html_report += "</body></html>"

    md_report = (
        f"# Bug Bounty Report\n\nGenerated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"Total findings: {len(findings)}\n\n---\n\n"
    )
    for finding in findings:
        md_report += (
            f"## {finding.get('vuln_type', 'Unknown')} - {finding.get('severity', 'Unknown')}\n\n"
            f"- URL: {finding.get('url', 'N/A')}\n"
            f"- Description: {finding.get('description', 'N/A')}\n\n---\n\n"
        )

    col_html, col_md = st.columns(2)
    with col_html:
        st.download_button(
            "📥 Download HTML Report",
            data=html_report,
            file_name=f"bug_bounty_report_{timestamp}.html",
            mime="text/html",
            use_container_width=True,
        )
    with col_md:
        st.download_button(
            "📥 Download Markdown Report",
            data=md_report,
            file_name=f"bug_bounty_report_{timestamp}.md",
            mime="text/markdown",
            use_container_width=True,
        )
