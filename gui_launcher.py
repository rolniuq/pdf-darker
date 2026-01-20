"""GUI entry point for PDF Editor application."""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pdf_editor.gui.main_window import main

if __name__ == "__main__":
    sys.exit(main())