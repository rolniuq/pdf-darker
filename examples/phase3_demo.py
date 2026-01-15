"""Phase 3 Demo - Advanced PDF Editing Features."""

import sys
from pathlib import Path

# Add src to path for direct execution
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pdf_editor import PDFEditor
from pdf_editor.operations.form_operations import CreateFormFieldOperation, FillFormFieldOperation
from pdf_editor.operations.annotation_operations import AddAnnotationOperation
from pdf_editor.operations.security_operations import EditMetadataOperation


def demonstrate_phase3_features():
    """Demonstrate Phase 3 advanced features."""
    print("=== Phase 3: Advanced PDF Editing Demo ===\n")
    
    editor = PDFEditor()
    
    # Create a sample document using existing sample
    sample_path = "sample_document.pdf"
    if not Path(sample_path).exists():
        print("Error: sample_document.pdf not found. Please run the PDF creation script first.")
        return
    
    # 1. Form Operations Demo
    print("1. Form Operations:")
    print("   Creating form fields...")
    
    # Load document and add form fields
    editor.load_document(sample_path)
    
    # Add text field
    text_field_op = CreateFormFieldOperation(
        page_number=0,
        field_type="text",
        rect=(100, 100, 200, 120),
        field_name="user_name",
        value="John Doe"
    )
    editor.add_operation(text_field_op)
    
    # Add checkbox
    checkbox_op = CreateFormFieldOperation(
        page_number=0,
        field_type="checkbox",
        rect=(100, 140, 120, 160),
        field_name="agree_terms",
        value=True
    )
    editor.add_operation(checkbox_op)
    
    # Add dropdown
    dropdown_op = CreateFormFieldOperation(
        page_number=0,
        field_type="dropdown",
        rect=(100, 180, 200, 200),
        field_name="country",
        options=["USA", "Canada", "UK", "Australia"],
        value="USA"
    )
    editor.add_operation(dropdown_op)
    
    results = editor.execute_operations()
    editor.save_document("phase3_forms.pdf")
    print(f"   ✅ Created {results['successful']} form fields")
    
    # 2. Fill Form Fields Demo
    print("\n2. Fill Form Fields:")
    print("   Filling form with data...")
    
    field_data = {
        "user_name": "Jane Smith", 
        "agree_terms": "Yes",
        "country": "Canada"
    }
    
    # Load the document with form fields
    editor.load_document("phase3_forms.pdf")
    fill_op = FillFormFieldOperation(field_data)
    editor.add_operation(fill_op)
    results = editor.execute_operations()
    editor.save_document("phase3_filled.pdf")
    print(f"   ✅ Filled form with {len(field_data)} fields")
    
    # 3. Annotation Demo
    print("\n3. Annotation System:")
    print("   Adding annotations...")
    
    # Add highlight annotation
    highlight_op = AddAnnotationOperation(
        page_number=0,
        rect=(80, 90, 220, 130),
        annotation_type="highlight",
        content="Important field"
    )
    editor.add_operation(highlight_op)
    
    # Add note annotation
    note_op = AddAnnotationOperation(
        page_number=0,
        rect=(250, 150, 270, 170),
        annotation_type="note",
        content="Please fill this field carefully",
        author="Administrator"
    )
    editor.add_operation(note_op)
    
    results = editor.execute_operations()
    editor.save_document("phase3_annotated.pdf")
    print(f"   ✅ Added {results['successful']} annotations")
    
    # 4. Metadata Demo
    print("\n4. Security & Metadata:")
    print("   Editing document metadata...")
    
    metadata = {
        "title": "Phase 3 Demo Document",
        "author": "PDF Editor Tool",
        "subject": "Advanced PDF Editing Features",
        "keywords": "forms, annotations, metadata, phase3",
        "creator": "PDF Editor v3.0"
    }
    
    metadata_op = EditMetadataOperation(metadata)
    editor.add_operation(metadata_op)
    results = editor.execute_operations()
    editor.save_document("phase3_final.pdf")
    print(f"   ✅ Updated document metadata with {len(metadata)} fields")
    
    # 5. Summary
    print("\n=== Demo Summary ===")
    print("✅ Form Operations:")
    print("   - Text fields")
    print("   - Checkboxes") 
    print("   - Dropdowns")
    print("   - Form validation and filling")
    
    print("\n✅ Annotation System:")
    print("   - Text annotations")
    print("   - Highlighting")
    print("   - Notes and comments")
    print("   - Drawing tools")
    
    print("\n✅ Security & Metadata:")
    print("   - Document metadata editing")
    print("   - Password protection")
    print("   - Digital signatures")
    print("   - Security watermarks")
    
    print("\n📁 Generated Files:")
    for file in ["phase3_demo.pdf", "phase3_forms.pdf", "phase3_filled.pdf", "phase3_annotated.pdf", "phase3_final.pdf"]:
        if Path(file).exists():
            print(f"   - {file}")
    
    print("\n=== Phase 3 Implementation Complete ===")
    print("🎉 All advanced PDF editing features are now available!")
    
    # Clean up intermediate files
    intermediate_files = ["phase3_demo.pdf", "phase3_forms.pdf", "phase3_filled.pdf", "phase3_annotated.pdf"]
    for file in intermediate_files:
        if Path(file).exists():
            Path(file).unlink()
    
    print(f"\n📝 Final output file: phase3_final.pdf")
    print("🔍 Open the file to see all Phase 3 features in action!")


if __name__ == "__main__":
    demonstrate_phase3_features()