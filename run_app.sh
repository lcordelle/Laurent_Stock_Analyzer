#!/bin/bash
# Run the Stock Analyzer app from the correct directory
cd "$(dirname "$0")"
exec python3 -m streamlit run main.py "$@"
