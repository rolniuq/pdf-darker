#!/usr/bin/env python3
"""
Demonstration of text operations functionality.
This script shows how to use the text editing features of the PDF editor.
"""

import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pdf_editor.core.document import PDFDocument
from pdf_editor.core.base import OperationManager
from pdf_editor.operations.text_operations import (
    AddTextOperation, 
    HighlightTextOperation, 
    AddAnnotationOperation,
    AddTextBoxOperation,
    ReplaceTextOperation,
    DeleteTextOperation
)

def demonstrate_text_operations():
    """Demonstrate various text operations on a PDF."""
    
    print("🔧 PDF Text Operations Demo")
    print("=" * 40)
    
    # Create a simple PDF document for demonstration
    # In practice, you would load an existing PDF
    input_pdf = Path("sample_document.pdf")
    
    if not input_pdf.exists():
        print(f"❌ Sample PDF not found: {input_pdf}")
        print("Please create or provide a sample PDF file to test with.")
        return
    
    try:
        # Load the PDF document
        doc = PDFDocument(input_pdf)
        print(f"✅ Loaded PDF: {input_pdf.name}")
        print(f"📄 Pages: {doc.page_count}")
        
        # Create operation manager
        manager = OperationManager()
        
        # Example 1: Add text to a page
        print("\n1️⃣ Adding text to page 0...")
        add_text_op = AddTextOperation(
            page_number=0,
            text="This is added text!",
            position=(100, 100),
            fontsize=12,
            color=(1, 0, 0)  # Red text
        )
        manager.add_operation(add_text_op)
        
        # Example 2: Highlight text
        print("2️⃣ Highlighting text...")
        highlight_op = HighlightTextOperation(
            search_text="important",
            color=(1, 1, 0),  # Yellow highlight
            page_numbers=[0]  # Only first page
        )
        manager.add_operation(highlight_op)
        
        # Example 3: Add annotation
        print("3️⃣ Adding annotation...")
        annotation_op = AddAnnotationOperation(
            page_number=0,
            position=(200, 200),
            text="This is a note about the document",
            annotation_type="note",
            author="PDF Editor Demo"
        )
        manager.add_operation(annotation_op)
        
        # Example 4: Add text box
        print("4️⃣ Adding text box...")
        textbox_op = AddTextBoxOperation(
            page_number=0,
            rect=(50, 300, 250, 350),
            text="This is a text box with a border",
            bgcolor=(0.9, 0.9, 0.9),  # Light gray background
            border=True,
            border_color=(0, 0, 1)  # Blue border
        )
        manager.add_operation(textbox_op)
        
        # Example 5: Replace text (simplified version)
        print("5️⃣ Replacing text...")
        replace_op = ReplaceTextOperation(
            search_text="old text",
            replace_text="new text",
            page_numbers=[0]
        )
        manager.add_operation(replace_op)
        
        # Execute all operations
        print("\n🚀 Executing operations...")
        results = manager.execute_operations(doc)
        
        # Show results
        summary = manager.get_results_summary()
        print(f"\n📊 Results Summary:")
        print(f"   Total operations: {summary['total']}")
        print(f"   Successful: {summary['successful']}")
        print(f"   Failed: {summary['failed']}")
        print(f"   Success rate: {summary['success_rate']:.1f}%")
        
        # Save the modified document
        if doc.is_modified:
            output_path = input_pdf.parent / f"modified_{input_pdf.name}"
            doc.save(output_path)
            print(f"💾 Saved modified PDF to: {output_path}")
        else:
            print("ℹ️ No modifications were made to the document")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    print("\n✨ Text operations demo completed!")
    return True

if __name__ == "__main__":
    demonstrate_text_operations()