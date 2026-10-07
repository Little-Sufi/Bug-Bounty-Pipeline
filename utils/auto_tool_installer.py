#!/usr/bin/env python3
import os
import sys
import subprocess
import platform

def run_command(cmd, check=True):
    try:
        print(f"[*] Running: {cmd}")
        subprocess.run(cmd, shell=True, check=check)
        return True
    except Exception as e:
        print(f"[-] Error: {e}")
        return False

def install_amass():
    print("\n[*] Checking Amass...")
    if run_command("amass --version", check=False):
        print("[+] Amass already installed!")
        return
    print("[*] Installing Amass...")
    if platform.system() == "Windows":
        print("[!] On Windows, download Amass from https://github.com/OWASP/Amass/releases")
    else:
        run_command("go install -v github.com/OWASP/Amass/v3/...@master")

def install_nuclei():
    print("\n[*] Checking Nuclei...")
    if run_command("nuclei --version", check=False):
        print("[+] Nuclei already installed!")
        return
    print("[*] Installing Nuclei...")
    if platform.system() == "Windows":
        print("[!] On Windows, download Nuclei from https://github.com/projectdiscovery/nuclei/releases")
    else:
        run_command("go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest")

def install_python_deps():
    print("\n[*] Installing Python dependencies...")
    requirements = ["pyyaml", "requests", "psutil", "dnspython"]
    run_command(f"{sys.executable} -m pip install {' '.join(requirements)}")

def main():
    print("=" * 60)
    print("🐛 Bug Bounty Pipeline - Auto Tool Installer")
    print("=" * 60)
    print("\nWARNING: For LAB USE ONLY!")
    confirm = input("Continue? (y/N): ").strip().lower()
    if confirm != "y":
        print("Exiting.")
        return

    install_python_deps()
    install_amass()
    install_nuclei()

    print("\n[+] Installation complete!")

if __name__ == "__main__":
    main()
