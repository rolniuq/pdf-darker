"""Enhanced example showing dark mode integration."""

import sys
from pathlib import Path

# Add src to path for direct execution
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pdf_editor import PDFEditor
from pdf_editor.operations import DarkModeOperation, RotatePageOperation
from pdf_editor.operations.dark_mode_legacy import convert_pdf_to_dark


def demonstrate_dark_mode_integration():
    """Demonstrate dark mode conversion in both API and CLI style."""
    print("=== Dark Mode Integration Demo ===\n")
    
    # Method 1: Using new operations API (recommended)
    print("1. Using PDF Editor API:")
    try:
        editor = PDFEditor()
        
        # Load a PDF (create dummy if needed)
        document = editor.load_document("input.pdf")
        
        # Add dark mode operation with custom settings
        dark_op = DarkModeOperation(dpi=300, quality=95, verbose=True)
        editor.add_operation(dark_op)
        
        # Execute and save
        results = editor.execute_operations()
        editor.save_document("output_api_dark.pdf")
        
        print(f"✅ API Mode: {results['successful']}/{results['total']} operations successful")
        print("📁 Saved: output_api_dark.pdf\n")
        
    except FileNotFoundError:
        print("⚠️  input.pdf not found - API demo skipped\n")
    
    # Method 2: Using legacy function (backward compatible)
    print("2. Using Legacy Function:")
    try:
        convert_pdf_to_dark("input.pdf", "output_legacy_dark.pdf", dpi=300, verbose=True)
        print("✅ Legacy Mode: Conversion completed")
        print("📁 Saved: output_legacy_dark.pdf\n")
        
    except FileNotFoundError:
        print("⚠️  input.pdf not found - legacy demo skipped\n")
    
    # Method 3: Combining with other operations
    print("3. Combining Dark Mode with Other Operations:")
    try:
        editor = PDFEditor()
        document = editor.load_document("input.pdf")
        
        # Rotate first page AND convert to dark mode
        rotate_op = RotatePageOperation(page_number=0, angle=90)
        dark_op = DarkModeOperation(dpi=200, quality=85, verbose=True)
        
        editor.add_operation(rotate_op)
        editor.add_operation(dark_op)
        
        results = editor.execute_operations()
        editor.save_document("output_combined.pdf")
        
        print(f"✅ Combined: {results['successful']}/{results['total']} operations successful")
        print("📁 Saved: output_combined.pdf\n")
        
    except FileNotFoundError:
        print("⚠️  input.pdf not found - combined demo skipped\n")
    
    print("=== Demo Complete ===")
    print("\nBenefits of integrated dark mode:")
    print("• ✅ Part of operations system")
    print("• ✅ Configurable parameters")
    print("• ✅ Progress tracking") 
    print("• ✅ Error handling")
    print("• ✅ Can be combined with other operations")
    print("• ✅ Backward compatible with legacy function")


if __name__ == "__main__":
    demonstrate_dark_mode_integration()