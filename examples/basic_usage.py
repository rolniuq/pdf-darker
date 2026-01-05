"""Example usage of the PDF Editor library."""

from pdf_editor import PDFEditor
from pdf_editor.operations import DarkModeOperation, RotatePageOperation, AddTextOperation


def example_dark_mode():
    """Example: Convert PDF to dark mode."""
    editor = PDFEditor()
    
    # Load a PDF
    document = editor.load_document("input.pdf")
    
    # Add dark mode operation
    operation = DarkModeOperation(dpi=300, quality=95)
    editor.add_operation(operation)
    
    # Execute operations
    results = editor.execute_operations()
    
    # Save the document
    editor.save_document("output_dark.pdf")
    
    print(f"Dark mode conversion: {results['successful']}/{results['total']} operations successful")


def example_page_operations():
    """Example: Page manipulation operations."""
    editor = PDFEditor()
    
    # Load a PDF
    document = editor.load_document("input.pdf")
    
    # Rotate first page
    rotate_op = RotatePageOperation(page_number=0, angle=90)
    editor.add_operation(rotate_op)
    
    # Add text to second page
    add_text_op = AddTextOperation(
        page_number=1, 
        text="This is added text", 
        position=(100, 100)
    )
    editor.add_operation(add_text_op)
    
    # Execute operations
    results = editor.execute_operations()
    
    # Save the document
    editor.save_document("output_edited.pdf")
    
    print(f"Page operations: {results['successful']}/{results['total']} operations successful")


if __name__ == "__main__":
    print("Run examples with: python examples/basic_usage.py")
    print("Make sure you have input.pdf in the current directory")