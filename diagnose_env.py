#!/usr/bin/env python3
# Python version of environment diagnostic
import os
import sys
import subprocess
import platform

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(BASE_DIR, "env.txt")


def test_python(path: str) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            [path, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return (result.returncode == 0, result.stdout.strip() if result.returncode == 0 else "Failed")
    except Exception as e:
        return (False, str(e))


def find_python() -> list[tuple[str, str]]:
    candidates = []
    if platform.system() == "Windows":
        common_paths = [
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python\Python313\python.exe"),
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python\Python312\python.exe"),
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python\Python311\python.exe"),
            r"C:\Python313\python.exe",
            r"C:\Python312\python.exe",
            r"C:\Python311\python.exe",
            "py",
            "python3",
            "python",
        ]
    else:
        common_paths = [
            "/usr/bin/python3",
            "/usr/local/bin/python3",
            "python3",
            "python",
            "py",
        ]
    # Also try sys.executable first
    if hasattr(sys, "executable") and sys.executable:
        if os.path.exists(sys.executable):
            common_paths.insert(0, sys.executable)

    working_candidates = []
    for path in common_paths:
        if not path:
            continue
        print(f"Checking: {path}")
        ok, info = test_python(path)
        if ok:
            print(f"[+] WORKING: {path} - {info}")
            working_candidates.append((path, info))
        else:
            print(f"[-] BROKEN: {path}")
    return working_candidates


def main():
    print("=" * 60)
    print("Bug Bounty Pipeline: Python Diagnostic")
    print("=" * 60)
    print()
    print("WARNING: FOR AUTHORIZED LAB USE ONLY!")
    print()

    working_candidates = find_python()
    if not working_candidates:
        print("\n" + "=" * 60)
        print("NO WORKING PYTHON FOUND AUTOMATICALLY")
        print("=" * 60)
        print()
        print("Please install Python 3.11 or newer from: https://python.org/downloads/")
        print("\nOnce installed, re-run this diagnostic, or manually create env.txt")
        print("with one line: PYTHON_CMD=C:\\full\\path\\to\\your\\python.exe")
        return 1

    print("\n" + "=" * 60)
    print("Found working Python installations!")
    print("=" * 60)

    # Use first working candidate
    chosen_path, chosen_info = working_candidates[0]
    if len(working_candidates) > 1:
        print(f"\nFound {len(working_candidates)} working versions; using first one:\n")

    print(f"Using: {chosen_path}")
    print(f"Version: {chosen_info}")

    # Save to env.txt
    with open(ENV_FILE, "w") as f:
        f.write(f"PYTHON_CMD={chosen_path}\n")
    print(f"\nSaved to {ENV_FILE}")
    print()
    print("Now you can run run.bat!")
    return 0


if __name__ == "__main__":
    exit(main())
