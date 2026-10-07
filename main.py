#!/usr/bin/env python3
# ==============================================================================
# 🐛 BUG BOUNTY PIPELINE: MAIN LAUNCHER
# ==============================================================================
import os
import sys

def main():
    # Insert utils path
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.join(base_dir, "utils"))
    
    try:
        from interactive_dashboard import InteractiveDashboard
        dashboard = InteractiveDashboard()
        dashboard.show_main_menu()
    except KeyboardInterrupt:
        print("\n\n[!] Operation cancelled by user. Exiting.")
        sys.exit(0)
    except Exception as e:
        print(f"\n[!] Error launching dashboard: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
