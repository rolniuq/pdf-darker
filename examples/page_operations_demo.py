#!/usr/bin/env python3
"""
Demonstration of page manipulation functionality.
This script shows how to use the page editing features of the PDF editor.
"""

import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pdf_editor.core.document import PDFDocument
from pdf_editor.core.manager import OperationManager
from pdf_editor.operations.page_operations import (
    RotatePageOperation,
    DeletePageOperation,
    ReorderPagesOperation,
    InsertPageOperation,
    ExtractPagesOperation,
    MergeDocumentsOperation,
    SplitDocumentOperation
)

def demonstrate_page_operations():
    """Demonstrate various page operations on a PDF."""
    
    print("🔧 PDF Page Operations Demo")
    print("=" * 40)
    
    # Create a simple PDF document for demonstration
    input_pdf = Path("sample_document.pdf")
    
    if not input_pdf.exists():
        print(f"❌ Sample PDF not found: {input_pdf}")
        print("Please create or provide a sample PDF file to test with.")
        return
    
    try:
        # Load the PDF document
        doc = PDFDocument(input_pdf)
        print(f"✅ Loaded PDF: {input_pdf.name}")
        print(f"📄 Original pages: {doc.page_count}")
        
        # Create operation manager
        manager = OperationManager()
        
        # Example 1: Rotate a page
        if doc.page_count > 1:
            print("\n1️⃣ Rotating page 1 by 90 degrees...")
            rotate_op = RotatePageOperation(
                page_number=1,
                angle=90
            )
            manager.add_operation(rotate_op)
        
        # Example 2: Insert a blank page
        print("2️⃣ Inserting blank page at position 2...")
        insert_op = InsertPageOperation(
            insert_position=min(2, doc.page_count),
            width=612,  # Letter width
            height=792  # Letter height
        )
        manager.add_operation(insert_op)
        
        # Example 3: Reorder pages (if we have enough pages)
        if doc.page_count >= 3:
            print("3️⃣ Reordering pages...")
            # Simple reorder: move last page to first position
            new_order = [doc.page_count - 1] + list(range(doc.page_count - 1))
            reorder_op = ReorderPagesOperation(new_order=new_order)
            manager.add_operation(reorder_op)
        
        # Example 4: Extract specific pages
        if doc.page_count > 2:
            print("4️⃣ Extracting pages 0 and 1...")
            extract_dir = Path("extracted_pages")
            extract_op = ExtractPagesOperation(
                page_numbers=[0, 1],
                output_path=str(extract_dir / "extracted_pages.pdf")
            )
            manager.add_operation(extract_op)
        
        # Example 5: Split document
        if doc.page_count > 3:
            print("5️⃣ Splitting document...")
            split_op = SplitDocumentOperation(
                split_points=[2],  # Split after page 2
                output_dir=str(Path("splits")),
                naming_pattern="part_{start}_{end}.pdf"
            )
            manager.add_operation(split_op)
        
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
            output_path = input_pdf.parent / f"modified_pages_{input_pdf.name}"
            doc.save(output_path)
            print(f"💾 Saved modified PDF to: {output_path}")
        else:
            print("ℹ️ No modifications were made to the document")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    print("\n✨ Page operations demo completed!")
    return True

def demonstrate_merge_operations():
    """Demonstrate merging multiple PDFs."""
    
    print("\n🔧 PDF Merge Operations Demo")
    print("=" * 40)
    
    # For this demo, we'll simulate having multiple PDFs
    input_pdf = Path("sample_document.pdf")
    
    if not input_pdf.exists():
        print(f"❌ Sample PDF not found: {input_pdf}")
        return
    
    try:
        # Create duplicate PDFs for merging demo
        import shutil
        pdf2 = Path("sample_document_copy.pdf")
        pdf3 = Path("sample_document_copy2.pdf")
        
        shutil.copy2(input_pdf, pdf2)
        shutil.copy2(input_pdf, pdf3)
        
        # Load the main PDF
        doc = PDFDocument(input_pdf)
        print(f"✅ Loaded main PDF: {input_pdf.name}")
        
        # Create operation manager
        manager = OperationManager()
        
        # Merge documents
        print("🔗 Merging documents...")
        merge_op = MergeDocumentsOperation(
            source_documents=[str(pdf2), str(pdf3)],
            output_path="merged_document.pdf",
            insert_position=doc.page_count
        )
        manager.add_operation(merge_op)
        
        # Execute operations
        results = manager.execute_operations(doc)
        
        # Show results
        summary = manager.get_results_summary()
        print(f"\n📊 Merge Results:")
        print(f"   Total operations: {summary['total']}")
        print(f"   Successful: {summary['successful']}")
        print(f"   Failed: {summary['failed']}")
        
        # Save the merged document
        if doc.is_modified:
            output_path = "merged_output.pdf"
            doc.save(output_path)
            print(f"💾 Saved merged PDF to: {output_path}")
        
        # Clean up temporary files
        pdf2.unlink(missing_ok=True)
        pdf3.unlink(missing_ok=True)
        
    except Exception as e:
        print(f"❌ Error during merge demo: {e}")
        return False
    
    print("✨ Merge operations demo completed!")
    return True

if __name__ == "__main__":
    demonstrate_page_operations()
    demonstrate_merge_operations()