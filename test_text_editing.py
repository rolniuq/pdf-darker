#!/usr/bin/env python3
"""Test text editing functionality."""

import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from pdf_editor.core.editor import PDFEditor
from pdf_editor.operations.text_operations import AddTextOperation, HighlightTextOperation

def test_text_editing():
    """Test text editing on sample PDF."""
    
    # Input and output files
    input_file = "sample_document.pdf"
    output_file = "test_text_editing.pdf"
    
    if not Path(input_file).exists():
        print(f"Error: {input_file} not found")
        return False
    
    try:
        # Create editor and load document
        editor = PDFEditor()
        editor.load_document(input_file)
        
        # Debug: Check document properties
        doc = editor.current_document
        print(f"Document loaded: {doc}")
        print(f"Document has _doc: {hasattr(doc, '_doc')}")
        print(f"Document page_count: {doc.page_count}")
        
        # Test 1: Add text to first page
        print("Testing: Add text to page 0...")
        add_text_op = AddTextOperation(
            page_number=0,
            text="This is test text added by PDF Editor!",
            position=(100, 100),
            fontsize=14,
            color=(0, 0, 1)  # Blue text
        )
        editor.add_operation(add_text_op)
        
        # Debug: Check operation validation manually
        print(f"Add text validation result: {add_text_op.validate(doc)}")
        
        # Test 2: Highlight existing text (if any)
        print("Testing: Highlight text...")
        highlight_op = HighlightTextOperation(
            search_text="the",  # Common word to highlight
            color=(1, 1, 0)  # Yellow highlight
        )
        editor.add_operation(highlight_op)
        
        # Execute operations
        print("Executing operations...")
        editor.execute_operations()
        
        # Save document
        success = editor.save_document(output_file)
        editor.close_document()
        
        print(f"✅ Text editing test completed!")
        print(f"   Save successful: {success}")
        print(f"   Expected output: {output_file}")
        
        # Check if file exists
        if Path(output_file).exists():
            print(f"   ✅ File exists: {Path(output_file).stat().st_size} bytes")
        else:
            print(f"   ❌ File not found: {output_file}")
        return True
        
    except Exception as e:
        print(f"❌ Text editing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_text_editing()
    sys.exit(0 if success else 1)