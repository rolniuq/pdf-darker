#!/usr/bin/env python3
"""Main entry point for PDF Editor CLI."""

import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from pdf_editor.cli.main import cli

if __name__ == "__main__":
    cli()