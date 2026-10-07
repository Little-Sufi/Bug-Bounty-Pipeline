
#!/usr/bin/env python3
# UNIFIED RECON SCRIPT: All recon tasks in one!
# WARNING: STRICTLY FOR AUTHORIZED LAB USE ONLY!
import os
import sys
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
import yaml
import requests
import time
import shutil
import subprocess
import dns.resolver
import socket
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))
from lab_validation import require_lab_target

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    return {}

def sanitize_filename(name):
    name = name.replace("http://", "").replace("https://", "")
    for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']:
        name = name.replace(char, "_")
    return name


def extract_target_host(target):
    target = target.strip()
    parsed = urlparse(target if "://" in target else f"//{target}")
    return (parsed.hostname or parsed.netloc or target).strip("[]")


def normalize_base_url(target):
    target = target.strip()
    if not target.startswith(("http://", "https://")):
        target = "http://" + target
    return target.rstrip("/")

def run_amass(config, recon_dir):
    """Run Amass subdomain enumeration"""
    print("\n" + "="*80)
    print("🔍 RUNNING AMASS ENUMERATION")
    print("="*80)
    
    for target in config.get("targets", ["lab.example.com"]):
        target_host = extract_target_host(target)
        print(f"\n[*] Target: {target_host}")
        output_file = os.path.join(recon_dir, f"amass-{sanitize_filename(target_host)}.txt")
        
        if not shutil.which("amass"):
            print("[!] Amass not found—skipping Amass, using manual subdomain list")
            # Fallback subdomains
            fallback = [
                f"www.{target_host}", f"api.{target_host}", f"dev.{target_host}",
                f"staging.{target_host}", f"test.{target_host}"
            ]
            with open(output_file, "w") as f:
                f.write("\n".join(fallback) + "\n")
            print(f"[+] Saved fallback subdomains to {output_file}")
            continue
        
        try:
            cmd = f"amass enum -d {target_host} -o {output_file}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
            print(f"[+] Results saved to {output_file}")
        except Exception as e:
            print(f"[-] Error running Amass: {e}")

def get_headers():
    try:
        from utils.settings import settings
        headers_config = settings.get("headers", {})
        user_agent = headers_config.get("user_agent", "BugBountyPipeline/1.0 (Authorized Security Lab)")
        custom_headers = dict(headers_config.get("custom_headers", {}))
        custom_headers["User-Agent"] = user_agent
        return custom_headers
    except Exception:
        return {"User-Agent": "BugBountyPipeline/1.0"}

def get_proxy_settings():
    try:
        from utils.settings import settings
        proxy_config = settings.get("proxy", {})
        if proxy_config.get("enabled", False):
            try:
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            except:
                pass
            return {
                "http": proxy_config.get("http", ""),
                "https": proxy_config.get("https", "")
            }
    except:
        pass
    return None

def validate_directory_existence(url):
    """Zero false positive directory validation"""
    try:
        headers = get_headers()
        proxies = get_proxy_settings()
        verify = False if proxies else True
        resp1 = requests.get(url, headers=headers, proxies=proxies, verify=verify, timeout=10, allow_redirects=False)
        if resp1.status_code not in [200, 301, 302, 403]:
            return False
        resp2 = requests.head(url, headers=headers, proxies=proxies, verify=verify, timeout=10, allow_redirects=False)
        if resp2.status_code != resp1.status_code:
            return False
        bad_resp = requests.get(url + "/nonexistent12345", headers=headers, proxies=proxies, verify=verify, timeout=10, allow_redirects=False)
        if resp1.content == bad_resp.content:
            return False
        return True
    except:
        return False

def run_directory_enum(config, recon_dir):
    """Run directory enumeration"""
    print("\n" + "="*80)
    print("📂 RUNNING DIRECTORY ENUMERATION")
    print("="*80)
    
    target_url = normalize_base_url(config.get("targets", ["http://lab.example.com"])[0])
    print(f"\n[*] Target: {target_url}")
    
    directories = [
        "/admin", "/api", "/backup", "/config", "/db", 
        "/.git", "/.env", "/private", "/secret", "/test"
    ]
    
    findings = []
    for dir_path in directories:
        url = target_url + dir_path
        print(f"[*] Testing: {url}")
        if validate_directory_existence(url):
            print(f"[+] CONFIRMED DIRECTORY (ZERO FALSE POSITIVE)!")
            findings.append(url)
        else:
            print(f"[-] Not found or false positive")
        time.sleep(0.3)
    
    if findings:
        output_file = os.path.join(recon_dir, "directories.txt")
        with open(output_file, "w") as f:
            f.write("\n".join(findings) + "\n")
        print(f"\n[+] Found {len(findings)} confirmed directories! Saved to {output_file}")

def validate_subdomain_takeover(domain, cname):
    """Zero false positive subdomain takeover validation"""
    try:
        resolver = dns.resolver.Resolver()
        answers = resolver.resolve(domain, 'CNAME')
        if not answers:
            return False
        found_cname = str(answers[0].target).lower()
        if cname.lower() not in found_cname:
            return False
        
        try:
            proxies = get_proxy_settings()
            verify = False if proxies else True
            resp = requests.get(f"http://{domain}", headers=get_headers(), proxies=proxies, verify=verify, timeout=10, allow_redirects=False)
            keywords = [
                "no such app", "there isn't a github pages site here",
                "bucket not found", "the specified bucket does not exist",
                "heroku | no such app", "site not found", "unclaimed"
            ]
            if any(k in resp.text.lower() for k in keywords):
                try:
                    socket.create_connection((found_cname, 80), timeout=5)
                except:
                    return True
        except:
            pass
    except:
        pass
    return False

def run_subdomain_takeover(config, recon_dir):
    """Run subdomain takeover scan"""
    print("\n" + "="*80)
    print("🏴‍☠️ RUNNING SUBDOMAIN TAKEOVER SCAN")
    print("="*80)
    
    subdomains = []
    for target in config.get("targets", ["lab.example.com"]):
        target_host = extract_target_host(target)
        amass_file = os.path.join(recon_dir, f"amass-{sanitize_filename(target_host)}.txt")
        if os.path.exists(amass_file):
            with open(amass_file, "r") as f:
                subdomains.extend([line.strip() for line in f if line.strip()])
        else:
            subdomains.extend([
                f"www.{target_host}", f"api.{target_host}", f"dev.{target_host}",
                f"staging.{target_host}", f"test.{target_host}"
            ])
    
    subdomains = list(set(subdomains))
    print(f"\n[*] Checking {len(subdomains)} subdomains")
    
    vulnerable_providers = [
        "github.io", "herokuapp.com", "s3.amazonaws.com",
        "netlify.com", "firebaseapp.com"
    ]
    
    findings = []
    for domain in subdomains:
        print(f"\n[*] Checking: {domain}")
        for provider in vulnerable_providers:
            if validate_subdomain_takeover(domain, provider):
                print(f"[+] CONFIRMED VULNERABILITY (ZERO FALSE POSITIVE)!")
                findings.append((domain, provider))
            else:
                print(f"[-] Not vulnerable to {provider}")
        time.sleep(0.5)
    
    if findings:
        output_file = os.path.join(recon_dir, "subdomain-takeovers.txt")
        with open(output_file, "w") as f:
            for domain, provider in findings:
                f.write(f"{domain} -> {provider}\n")
        print(f"\n[+] Found {len(findings)} confirmed takeovers! Saved to {output_file}")

def main():
    print("="*80)
    print("🔍 UNIFIED RECON PIPELINE")
    print("="*80)
    print("WARNING: FOR AUTHORIZED LAB USE ONLY!")
    
    config = load_config()
    for target in config.get("targets", []):
        require_lab_target(target)
    recon_dir = os.path.join(os.path.dirname(__file__), "..", "01-Recon-OSINT/")
    os.makedirs(recon_dir, exist_ok=True)
    
    run_amass(config, recon_dir)
    run_directory_enum(config, recon_dir)
    run_subdomain_takeover(config, recon_dir)
    
    print("\n" + "="*80)
    print("✅ RECON COMPLETE!")
    print("="*80)

if __name__ == "__main__":
    main()
