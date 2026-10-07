from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)
LOG_FILE = OUTPUT_DIR / "pipeline.log"
LAB_LOG_FILE = OUTPUT_DIR / "test_lab.log"
FINDINGS_FILE = OUTPUT_DIR / "findings.json"
STOP_FILE = OUTPUT_DIR / "pipeline.stop"