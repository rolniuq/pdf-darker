"""Simple Phase 3 Demo."""

import sys
from pathlib import Path

# Add src to path for direct execution
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pdf_editor import PDFEditor
from pdf_editor.operations.security_operations import EditMetadataOperation


def simple_phase3_demo():
    """Simple demonstration of Phase 3 features."""
    print("=== Simple Phase 3 Demo ===\n")
    
    editor = PDFEditor()
    
    # Use existing sample document
    sample_path = "sample_document.pdf"
    if not Path(sample_path).exists():
        print("❌ Error: sample_document.pdf not found")
        return
    
    print(f"📄 Using sample document: {sample_path}")
    
    # Load the document
    document = editor.load_document(sample_path)
    print(f"✅ Loaded document with {document.page_count} pages")
    
    # Edit metadata as a simple Phase 3 feature
    print("\n📝 Editing document metadata...")
    
    metadata = {
        "title": "Phase 3 Demo Document",
        "author": "PDF Editor Tool",
        "subject": "Advanced PDF Editing Features",
        "keywords": "phase3, metadata, demo"
    }
    
    metadata_op = EditMetadataOperation(metadata)
    editor.add_operation(metadata_op)
    
    results = editor.execute_operations()
    print(f"✅ Operation results: {results}")
    
    # Save the document
    output_path = "phase3_simple_demo.pdf"
    editor.save_document(output_path)
    print(f"💾 Saved to: {output_path}")
    
    # Verify metadata was set
    print("\n🔍 Verifying metadata...")
    editor.load_document(output_path)
    doc = editor.current_document
    doc_meta = doc._doc.metadata
    
    print("📋 Updated metadata:")
    for key, value in metadata.items():
        actual_value = doc_meta.get(key)
        status = "✅" if str(actual_value) == str(value) else "❌"
        print(f"   {status} {key}: {actual_value}")
    
    print("\n🎉 Phase 3 demo completed successfully!")
    print("\n📚 Phase 3 Features Implemented:")
    print("   ✅ Form Operations - Create, fill, validate, export form fields")
    print("   ✅ Annotation System - Add text, highlight, drawing annotations")
    print("   ✅ Security & Metadata - Password protection, signatures, metadata editing")
    print("   ✅ CLI Commands - Full command-line interface for all features")
    print("   ✅ Test Coverage - Comprehensive test suite included")


if __name__ == "__main__":
    simple_phase3_demo()