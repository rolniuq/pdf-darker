#!/usr/bin/env python3
"""Legacy dark mode converter - preserved for backward compatibility."""

import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from pdf_editor.operations.dark_mode_legacy import convert_pdf_to_dark

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python init.py input.pdf output_dark.pdf")
        sys.exit(1)

    input_pdf = sys.argv[1]
    output_pdf = sys.argv[2]
    convert_pdf_to_dark(input_pdf, output_pdf)