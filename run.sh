#!/bin/bash
echo "========================================"
echo "  Bug Bounty Pipeline - Linux/macOS"
echo "========================================"
echo ""
echo "WARNING: FOR AUTHORIZED LAB USE ONLY!"
echo ""

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi
source venv/bin/activate
echo "Installing dependencies..."
pip install -r requirements.txt
echo ""
echo "Choose mode:"
echo "1. Interactive GUI (Recommended)"
echo "2. CLI Pipeline"
echo ""
read -p "Enter your choice (1 or 2): " mode
if [ "$mode" = "1" ]; then
    echo "Starting GUI..."
    streamlit run app.py
else
    echo "Starting CLI pipeline..."
    python3 main.py
fi
