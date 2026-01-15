"""Test cases for Phase 3 features."""

import pytest
import tempfile
import os
from pathlib import Path

from src.pdf_editor.core.editor import PDFEditor
from src.pdf_editor.operations.form_operations import (
    CreateFormFieldOperation, FillFormFieldOperation
)
from src.pdf_editor.operations.annotation_operations import (
    AddAnnotationOperation
)
from src.pdf_editor.operations.security_operations import (
    EditMetadataOperation, SetPasswordOperation
)


class TestPhase3Features:
    """Test suite for Phase 3 advanced features."""
    
    @pytest.fixture
    def sample_pdf(self):
        """Create a sample PDF for testing."""
        editor = PDFEditor()
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            sample_path = f.name
        
        # Create a simple one-page PDF for testing
        doc = editor._create_blank_document(sample_path)
        
        yield sample_path
        
        # Cleanup
        if os.path.exists(sample_path):
            os.unlink(sample_path)
    
    def test_create_form_field(self, sample_pdf):
        """Test form field creation."""
        editor = PDFEditor()
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            output_path = f.name
        
        try:
            # Create a text field
            operation = CreateFormFieldOperation(
                page_number=0,
                field_type="text",
                rect=(100, 100, 200, 120),
                field_name="test_field",
                value="Default Value"
            )
            
            editor.load_document(sample_pdf)
            editor.add_operation(operation)
            result = editor.execute_operations()
            
            assert result == {'successful': 1, 'total': 1, 'failed': 0}
            
            # Save and verify field was created
            editor.save_document(output_path)
            
            # Reload document and check for form field
            editor.load_document(output_path)
            document = editor.current_document
            page = document.get_page(0)
            widgets = page.widgets()
            
            assert len(widgets) == 1
            assert widgets[0].field_name == "test_field"
            
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_fill_form_field(self, sample_pdf):
        """Test form field filling."""
        editor = PDFEditor()
        
        # First create a form field
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            intermediate_path = f.name
        
        create_op = CreateFormFieldOperation(
            page_number=0,
            field_type="text",
            rect=(100, 100, 200, 120),
            field_name="test_field"
        )
        
        editor.load_document(sample_pdf)
        editor.add_operation(create_op)
        editor.execute_operations()
        editor.save_document(intermediate_path)
        
        # Now fill the form field
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            output_path = f.name
        
        field_data = {"test_field": "Filled Value"}
        fill_op = FillFormFieldOperation(field_data)
        
        editor.load_document(intermediate_path)
        editor.add_operation(fill_op)
        result = editor.execute_operations()
        
        assert result == {'successful': 1, 'total': 1, 'failed': 0}
        editor.save_document(output_path)
        
        # Verify field was filled
        editor.load_document(output_path)
        document = editor.current_document
        page = document.get_page(0)
        widgets = page.widgets()
        
        assert len(widgets) == 1
        assert widgets[0].field_value == "Filled Value"
        
        # Cleanup
        for path in [intermediate_path, output_path]:
            if os.path.exists(path):
                os.unlink(path)
    
    def test_add_annotation(self, sample_pdf):
        """Test annotation addition."""
        editor = PDFEditor()
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            output_path = f.name
        
        try:
            operation = AddAnnotationOperation(
                page_number=0,
                rect=(100, 100, 200, 120),
                annotation_type="highlight",
                content="Test annotation",
                author="Test User",
                color=(1, 1, 0)
            )
            
            editor.load_document(sample_pdf)
            editor.add_operation(operation)
            result = editor.execute_operations()
            
            assert result == {'successful': 1, 'total': 1, 'failed': 0}
            editor.save_document(output_path)
            
            # Verify annotation was added
            editor.load_document(output_path)
            document = editor.current_document
            page = document.get_page(0)
            annotations = page.annots()
            
            assert len(annotations) > 0
            
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_edit_metadata(self, sample_pdf):
        """Test metadata editing."""
        editor = PDFEditor()
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            output_path = f.name
        
        try:
            metadata = {
                "title": "Test Document",
                "author": "Test Author",
                "subject": "Test Subject",
                "keywords": "test, pdf, phase3"
            }
            
            operation = EditMetadataOperation(metadata)
            
            editor.load_document(sample_pdf)
            editor.add_operation(operation)
            result = editor.execute_operations()
            
            assert result == {'successful': 1, 'total': 1, 'failed': 0}
            editor.save_document(output_path)
            
            # Verify metadata was set
            editor.load_document(output_path)
            document = editor.current_document
            doc_metadata = document._doc.metadata
            
            assert doc_metadata["title"] == "Test Document"
            assert doc_metadata["author"] == "Test Author"
            assert doc_metadata["subject"] == "Test Subject"
            assert doc_metadata["keywords"] == "test, pdf, phase3"
            
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_password_protection_validation(self, sample_pdf):
        """Test password protection parameter validation."""
        # Test invalid password (too short)
        with pytest.raises(ValueError):
            operation = SetPasswordOperation(user_password="123")
            editor = PDFEditor()
            editor.load_document(sample_pdf)
            operation.validate(editor.current_document)
        
        # Test invalid encryption strength
        with pytest.raises(ValueError):
            operation = SetPasswordOperation(
                user_password="validpassword",
                encryption_strength=512
            )
            editor = PDFEditor()
            editor.load_document(sample_pdf)
            operation.validate(editor.current_document)
    
    def test_form_field_validation(self, sample_pdf):
        """Test form field parameter validation."""
        editor = PDFEditor()
        editor.load_document(sample_pdf)
        document = editor.current_document
        
        # Test invalid page number
        with pytest.raises(ValueError):
            operation = CreateFormFieldOperation(
                page_number=999,
                field_type="text",
                rect=(100, 100, 200, 120),
                field_name="test"
            )
            operation.validate(document)
        
        # Test invalid field type
        with pytest.raises(ValueError):
            operation = CreateFormFieldOperation(
                page_number=0,
                field_type="invalid_type",
                rect=(100, 100, 200, 120),
                field_name="test"
            )
            operation.validate(document)
        
        # Test invalid rectangle
        with pytest.raises(ValueError):
            operation = CreateFormFieldOperation(
                page_number=0,
                field_type="text",
                rect=(100, 100),  # Too few coordinates
                field_name="test"
            )
            operation.validate(document)


if __name__ == "__main__":
    pytest.main([__file__])