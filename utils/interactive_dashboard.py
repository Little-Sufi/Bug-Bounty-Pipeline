#!/usr/bin/env python3
# ==============================================================================
# 🐛 BUG BOUNTY PIPELINE: ADVANCED INTERACTIVE DASHBOARD
# ==============================================================================
import os
import sys
import subprocess
import yaml
import json
from datetime import datetime

# ANSI Color Codes for beautiful UI
RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
CYAN = "\033[36m"
MAGENTA = "\033[35m"
BG_BLUE = "\033[44m"
BG_RED = "\033[41m"

class InteractiveDashboard:
    def __init__(self):
        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.scripts_dir = os.path.join(self.base_dir, "scripts")
        self.config_path = os.path.join(self.base_dir, "config.yaml")
        self.targets_path = os.path.join(self.base_dir, "targets.txt")
        self.state_path = os.path.join(self.base_dir, ".pipeline_state.json")

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def load_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, "r") as f:
                return yaml.safe_load(f) or {}
        return {}

    def save_config(self, config):
        with open(self.config_path, "w") as f:
            yaml.safe_dump(config, f, default_flow_style=False)

    def resolve_script_path(self, script_name):
        candidates = [
            os.path.join(self.base_dir, "scanners", script_name),
            os.path.join(self.scripts_dir, script_name),
        ]
        for candidate in candidates:
            if os.path.exists(candidate):
                return candidate
        return candidates[0]

    def print_header(self, title):
        self.clear_screen()
        print(f"{CYAN}{BOLD}" + "=" * 70 + f"{RESET}")
        print(f"{CYAN}{BOLD}   🐛 BUG BOUNTY PIPELINE: {title.upper()} {RESET}")
        print(f"{CYAN}{BOLD}" + "=" * 70 + f"{RESET}\n")

    def get_status_summary(self):
        # Load pipeline state
        state = {}
        if os.path.exists(self.state_path):
            try:
                with open(self.state_path, "r") as f:
                    state = json.load(f)
            except Exception:
                pass
        
        completed = len(state.get("completed_scripts", []))
        failed = len(state.get("failed_scripts", []))
        
        config = self.load_config()
        targets = config.get("targets", [])
        target_str = targets[0] if targets else "None"
        if len(targets) > 1:
            target_str += f" (+{len(targets)-1} more)"

        summary = (
            f"   {BOLD}Target:{RESET} {YELLOW}{target_str}{RESET}  |  "
            f"{BOLD}Completed Tasks:{RESET} {GREEN}{completed}{RESET}  |  "
            f"{BOLD}Failures:{RESET} {RED}{failed}{RESET}"
        )
        return summary

    def show_main_menu(self):
        while True:
            self.clear_screen()
            print(f"{BLUE}{BOLD}" + "=" * 70 + f"{RESET}")
            print(f"{BLUE}{BOLD}   🐛 ULTIMATE BUG BOUNTY PIPELINE DASHBOARD {RESET}")
            print(f"{BLUE}{BOLD}" + "=" * 70 + f"{RESET}")
            print(self.get_status_summary())
            print(f"{BLUE}{BOLD}" + "-" * 70 + f"{RESET}")
            print(f"   {BOLD}1.{RESET} {CYAN}Reconnaissance & OSINT Module{RESET} (recon.py)")
            print(f"   {BOLD}2.{RESET} {GREEN}Custom Vulnerability Scanners{RESET} (XSS, SQLi, Traversal, Headers)")
            print(f"   {BOLD}3.{RESET} {YELLOW}Comprehensive OWASP Top 10 Suite{RESET} (owasp_top10_scanner.py)")
            print(f"   {BOLD}4.{RESET} {BOLD}Comprehensive Pipeline Control{RESET}")
            print(f"   {BOLD}5.{RESET} {BOLD}Target & Config Settings{RESET}")
            print(f"   {BOLD}6.{RESET} {BOLD}Reporting Console{RESET}")
            print(f"   {BOLD}0.{RESET} {RED}Exit Pipeline{RESET}")
            print(f"{BLUE}{BOLD}" + "=" * 70 + f"{RESET}")
            
            choice = input(f"{BOLD}Select option > {RESET}").strip()
            if choice == "1":
                self.run_script("recon.py")
            elif choice == "2":
                self.show_vuln_category_menu("Custom Vulnerability Scanners", [
                    ("custom_xss_scanner.py", "Custom Cross-Site Scripting (XSS) Scanner"),
                    ("custom_sqli_scanner.py", "Custom SQL Injection (SQLi) Scanner"),
                    ("custom_traversal_scanner.py", "Custom Path Traversal / LFI Scanner"),
                    ("custom_header_scanner.py", "Custom Security Header Scanner"),
                ])
            elif choice == "3":
                self.run_script("owasp_top10_scanner.py")
            elif choice == "4":
                self.show_pipeline_control_menu()
            elif choice == "5":
                self.show_config_menu()
            elif choice == "6":
                self.show_report_menu()
            elif choice == "0":
                print(f"\n{GREEN}[*] Exiting dashboard. Happy hunting!{RESET}\n")
                sys.exit(0)

    def show_vuln_category_menu(self, title, script_list):
        while True:
            self.print_header(title)
            for idx, (filename, description) in enumerate(script_list, 1):
                print(f"   {BOLD}{idx:2d}.{RESET} {description:<40} ({CYAN}{filename}{RESET})")
            print(f"   {BOLD} 0.{RESET} Back to Main Menu")
            print(f"\n" + "-" * 70)
            
            choice = input(f"{BOLD}Run scanner (Enter number) > {RESET}").strip()
            if choice == "0":
                break
            try:
                val = int(choice)
                if 1 <= val <= len(script_list):
                    self.run_script(script_list[val-1][0])
            except ValueError:
                pass

    def show_pipeline_control_menu(self):
        while True:
            self.print_header("Pipeline Control Panel")
            print(f"   {BOLD}1.{RESET} {GREEN}Run Full Automated Pipeline{RESET} (Handles resume and auto-fixes)")
            print(f"   {BOLD}2.{RESET} {YELLOW}Reset Pipeline State file{RESET} (Clears completed/failed tasks)")
            print(f"   {BOLD}3.{RESET} Install System Dependencies & Requirements")
            print(f"   {BOLD}0.{RESET} Back to Main Menu")
            print(f"\n" + "-" * 70)
            
            choice = input(f"{BOLD}Select option > {RESET}").strip()
            if choice == "1":
                self.run_pipeline()
            elif choice == "2":
                self.reset_pipeline_state()
            elif choice == "3":
                self.install_tools()
            elif choice == "0":
                break

    def run_pipeline(self):
        self.clear_screen()
        print(f"{YELLOW}[*] Starting Full Automated Pipeline (run-full-pipeline.py)...{RESET}\n")
        pipeline_path = os.path.join(self.base_dir, "run-full-pipeline.py")
        if os.path.exists(pipeline_path):
            try:
                subprocess.run([sys.executable, pipeline_path], cwd=self.base_dir)
            except Exception as e:
                print(f"{RED}[-] Error starting pipeline: {e}{RESET}")
        else:
            print(f"{RED}[-] Error: run-full-pipeline.py not found at {pipeline_path}{RESET}")
        input(f"\n{BOLD}Press Enter to return to menu...{RESET}")

    def reset_pipeline_state(self):
        if os.path.exists(self.state_path):
            try:
                os.remove(self.state_path)
                print(f"\n{GREEN}[+] Pipeline state reset successfully!{RESET}")
            except Exception as e:
                print(f"\n{RED}[-] Error resetting state: {e}{RESET}")
        else:
            print(f"\n{YELLOW}[*] No active state file found to reset.{RESET}")
        input(f"\n{BOLD}Press Enter to continue...{RESET}")

    def run_script(self, script_name):
        self.clear_screen()
        script_path = self.resolve_script_path(script_name)
        if os.path.exists(script_path):
            config = self.load_config()
            targets = config.get("targets", ["lab.example.com"])
            target = targets[0] if targets else "lab.example.com"
            
            print(f"{YELLOW}[*] Preparing script {script_name} for target {target}...{RESET}")
            
            # Use ScriptAdapter
            try:
                sys.path.insert(0, os.path.join(self.base_dir, "utils"))
                from script_adapter import ScriptAdapter
                adapter = ScriptAdapter()
                script_to_run = adapter.adapt_script(script_path, target)
            except Exception as e:
                print(f"{YELLOW}[!] Adaptation failed, running original script: {e}{RESET}")
                script_to_run = script_path
                
            print(f"{YELLOW}[*] Executing: {os.path.basename(script_to_run)}...{RESET}\n")
            try:
                subprocess.run([sys.executable, script_to_run], cwd=os.path.dirname(script_path))
            except Exception as e:
                print(f"{RED}[-] Script crashed: {e}{RESET}")
            finally:
                # Clean up adapted script if it was created
                if script_to_run != script_path and os.path.exists(script_to_run):
                    try:
                        os.remove(script_to_run)
                    except:
                        pass
        else:
            print(f"{RED}[-] Error: Script {script_name} not found at {script_path}{RESET}")
        input(f"\n{BOLD}Press Enter to continue...{RESET}")

    def show_config_menu(self):
        while True:
            self.print_header("Settings & Targets")
            config = self.load_config()
            targets = config.get("targets", [])
            print(f"   {BOLD}Current Targets:{RESET}")
            if not targets:
                print(f"      {RED}None configured!{RESET}")
            else:
                for idx, t in enumerate(targets, 1):
                    print(f"      - [{idx}] {YELLOW}{t}{RESET}")
            
            print(f"\n   {BOLD}Researcher:{RESET} {config.get('report', {}).get('researcher_name', 'Not Specified')}")
            print(f"   {BOLD}Company:{RESET}    {config.get('report', {}).get('company_name', 'Not Specified')}")
            print(f"\n   {BOLD}Options:{RESET}")
            print(f"      {BOLD}1.{RESET} Add Target Domain")
            print(f"      {BOLD}2.{RESET} Clear Targets")
            print(f"      {BOLD}3.{RESET} Edit Researcher Details")
            print(f"      {BOLD}0.{RESET} Back to Main Menu")
            print(f"\n" + "-" * 70)
            
            choice = input(f"{BOLD}Select option > {RESET}").strip()
            if choice == "1":
                new_target = input("Enter target domain (e.g. target.com): ").strip()
                if new_target:
                    targets.append(new_target)
                    config["targets"] = list(set(targets))
                    self.save_config(config)
                    # Write to targets.txt as well
                    with open(self.targets_path, "w") as f:
                        f.write("\n".join(config["targets"]) + "\n")
                    print(f"{GREEN}[+] Target added!{RESET}")
            elif choice == "2":
                config["targets"] = []
                self.save_config(config)
                if os.path.exists(self.targets_path):
                    with open(self.targets_path, "w") as f:
                        f.write("")
                print(f"{GREEN}[+] Targets cleared!{RESET}")
            elif choice == "3":
                name = input("Enter Researcher Name: ").strip()
                comp = input("Enter Company Name: ").strip()
                if "report" not in config:
                    config["report"] = {}
                if name:
                    config["report"]["researcher_name"] = name
                if comp:
                    config["report"]["company_name"] = comp
                self.save_config(config)
                print(f"{GREEN}[+] Details updated!{RESET}")
            elif choice == "0":
                break

    def show_report_menu(self):
        self.print_header("Reporting Console")
        try:
            from report_generator import ReportGenerator
            gen = ReportGenerator()
            findings = gen.load_findings()
            print(f"{GREEN}[+] Successfully scanned active findings!{RESET}")
            print(f"   - Total Vulnerabilities Found: {BOLD}{len(findings)}{RESET}")
            
            # Generate reports
            gen.save_report(findings, format="html")
            gen.save_report(findings, format="markdown")
            print(f"\n{GREEN}[+] Generated reports in 04-Reporting/ directory!{RESET}")
        except Exception as e:
            print(f"{RED}[-] Failed to generate report: {e}{RESET}")
        input(f"\n{BOLD}Press Enter to return to main menu...{RESET}")

    def install_tools(self):
        self.clear_screen()
        print(f"{YELLOW}[*] Installing dependencies...{RESET}\n")
        try:
            installer_path = os.path.join(self.base_dir, "utils", "auto_tool_installer.py")
            subprocess.run([sys.executable, installer_path], cwd=self.base_dir)
        except Exception as e:
            print(f"{RED}[-] Installer error: {e}{RESET}")
        input(f"\n{BOLD}Press Enter to return to menu...{RESET}")

if __name__ == "__main__":
    dashboard = InteractiveDashboard()
    dashboard.show_main_menu()
