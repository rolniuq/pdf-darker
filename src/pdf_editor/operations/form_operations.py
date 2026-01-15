"""Form operations for PDF editing."""

from typing import Any, Dict
import fitz  # PyMuPDF
from datetime import datetime

from ..core.base import BaseOperation, OperationType, OperationResult, PDFDocument


class FormOperation(BaseOperation):
    """Base class for form operations."""
    
    def __init__(self, operation_type: OperationType):
        super().__init__(operation_type)


class CreateFormFieldOperation(FormOperation):
    """Operation to create form fields in PDF."""
    
    def __init__(self, page_number: int, field_type: str, rect: tuple, 
                 field_name: str = None, value: str = None, 
                 options: list = None, **kwargs):
        super().__init__(OperationType.CREATE_FIELD)
        
        self.set_parameter("page_number", page_number)
        self.set_parameter("field_type", field_type)
        self.set_parameter("rect", rect)
        self.set_parameter("field_name", field_name)
        self.set_parameter("value", value)
        self.set_parameter("options", options or [])
        
        # Additional field properties
        for key, val in kwargs.items():
            self.set_parameter(key, val)
    
    def validate(self, document: PDFDocument) -> bool:
        """Validate form field creation parameters."""
        if not super().validate(document):
            return False
        
        page_number = self.get_parameter("page_number")
        field_type = self.get_parameter("field_type")
        rect = self.get_parameter("rect")
        field_name = self.get_parameter("field_name")
        
        # Validate page number
        if not isinstance(page_number, int) or page_number < 0 or page_number >= document.page_count:
            self.logger.error(f"Invalid page number: {page_number}")
            return False
        
        # Validate field type
        valid_types = ["text", "checkbox", "radio", "list", "dropdown", "signature"]
        if field_type not in valid_types:
            self.logger.error(f"Invalid field type: {field_type}. Must be one of {valid_types}")
            return False
        
        # Validate rectangle
        if (not isinstance(rect, tuple) or len(rect) != 4 or 
            not all(isinstance(x, (int, float)) for x in rect)):
            self.logger.error("Rect must be a tuple of 4 numbers (x0, y0, x1, y1)")
            return False
        
        # Validate field name
        if not field_name or not isinstance(field_name, str):
            self.logger.error("Field name must be a non-empty string")
            return False
        
        return True
    
    def execute(self, document: PDFDocument) -> OperationResult:
        """Execute form field creation."""
        try:
            page_number = self.get_parameter("page_number")
            field_type = self.get_parameter("field_type")
            rect = self.get_parameter("rect")
            field_name = self.get_parameter("field_name")
            value = self.get_parameter("value")
            options = self.get_parameter("options")
            
            page = document.get_page(page_number)
            
            # Create form field based on type
            if field_type == "text":
                widget = self._create_text_field(page, rect, field_name, value)
            elif field_type == "checkbox":
                widget = self._create_checkbox_field(page, rect, field_name, value)
            elif field_type == "radio":
                widget = self._create_radio_field(page, rect, field_name, options)
            elif field_type == "list":
                widget = self._create_list_field(page, rect, field_name, options)
            elif field_type == "dropdown":
                widget = self._create_dropdown_field(page, rect, field_name, options, value)
            elif field_type == "signature":
                widget = self._create_signature_field(page, rect, field_name)
            else:
                self.logger.error(f"Unsupported field type: {field_type}")
                return OperationResult.FAILED
            
            document.mark_modified()
            self.logger.info(f"Created {field_type} field '{field_name}' on page {page_number}")
            
            return OperationResult.SUCCESS
            
        except Exception as e:
            self.logger.error(f"Failed to create form field: {e}")
            return OperationResult.FAILED
    
    def _create_text_field(self, page, rect, field_name, value):
        """Create a text field widget."""
        widget = fitz.Widget()
        widget.field_name = field_name
        widget.field_type = fitz.PDF_WIDGET_TYPE_TEXT
        widget.rect = rect
        if value:
            widget.field_value = value
        
        # Set additional properties
        widget.field_flags = fitz.PDF_FIELD_IS_EDITABLE
        
        page.add_widget(widget)
        return widget
    
    def _create_checkbox_field(self, page, rect, field_name, value):
        """Create a checkbox field widget."""
        widget = fitz.Widget()
        widget.field_name = field_name
        widget.field_type = fitz.PDF_WIDGET_TYPE_CHECKBOX
        widget.rect = rect
        
        # Set checked state
        if value in [True, "true", "checked", "on"]:
            widget.field_value = "Yes"
        
        widget.field_flags = fitz.PDF_FIELD_IS_EDITABLE
        page.add_widget(widget)
        return widget
    
    def _create_radio_field(self, page, rect, field_name, options):
        """Create a radio button field widget."""
        widget = fitz.Widget()
        widget.field_name = field_name
        widget.field_type = fitz.PDF_WIDGET_TYPE_RADIOBUTTON
        widget.rect = rect
        
        widget.field_flags = fitz.PDF_FIELD_IS_EDITABLE
        page.add_widget(widget)
        return widget
    
    def _create_list_field(self, page, rect, field_name, options):
        """Create a list box field widget."""
        widget = fitz.Widget()
        widget.field_name = field_name
        widget.field_type = fitz.PDF_WIDGET_TYPE_LISTBOX
        widget.rect = rect
        widget.field_options = options
        
        widget.field_flags = fitz.PDF_FIELD_IS_EDITABLE
        page.add_widget(widget)
        return widget
    
    def _create_dropdown_field(self, page, rect, field_name, options, selected_value):
        """Create a dropdown field widget."""
        widget = fitz.Widget()
        widget.field_name = field_name
        widget.field_type = fitz.PDF_WIDGET_TYPE_COMBOBOX
        widget.rect = rect
        widget.field_options = options
        
        if selected_value and selected_value in options:
            widget.field_value = selected_value
        
        widget.field_flags = fitz.PDF_FIELD_IS_EDITABLE
        page.add_widget(widget)
        return widget
    
    def _create_signature_field(self, page, rect, field_name):
        """Create a signature field widget."""
        widget = fitz.Widget()
        widget.field_name = field_name
        widget.field_type = fitz.PDF_WIDGET_TYPE_SIGNATURE
        widget.rect = rect
        
        widget.field_flags = fitz.PDF_FIELD_IS_EDITABLE
        page.add_widget(widget)
        return widget


class FillFormFieldOperation(FormOperation):
    """Operation to fill form fields with data."""
    
    def __init__(self, field_data: Dict[str, Any], page_number: int = None):
        super().__init__(OperationType.FILL_FIELD)
        
        self.set_parameter("field_data", field_data)
        self.set_parameter("page_number", page_number)
    
    def validate(self, document: PDFDocument) -> bool:
        """Validate form field filling parameters."""
        if not super().validate(document):
            return False
        
        field_data = self.get_parameter("field_data")
        page_number = self.get_parameter("page_number")
        
        if not field_data or not isinstance(field_data, dict):
            self.logger.error("Field data must be a non-empty dictionary")
            return False
        
        if page_number is not None:
            if not isinstance(page_number, int) or page_number < 0 or page_number >= document.page_count:
                self.logger.error(f"Invalid page number: {page_number}")
                return False
        
        return True
    
    def execute(self, document: PDFDocument) -> OperationResult:
        """Execute form field filling."""
        try:
            field_data = self.get_parameter("field_data")
            page_number = self.get_parameter("page_number")
            
            total_filled = 0
            
            for page_idx in range(document.page_count):
                if page_number is not None and page_idx != page_number:
                    continue
                
                page = document.get_page(page_idx)
                widgets = page.widgets()
                
                for widget in widgets:
                    field_name = widget.field_name
                    if field_name in field_data:
                        value = field_data[field_name]
                        
                        # Set field value based on type
                        if widget.field_type == fitz.PDF_WIDGET_TYPE_TEXT:
                            widget.field_value = str(value)
                        elif widget.field_type == fitz.PDF_WIDGET_TYPE_CHECKBOX:
                            widget.field_value = "Yes" if value in [True, "true", "checked", "on"] else ""
                        elif widget.field_type == fitz.PDF_WIDGET_TYPE_COMBOBOX:
                            if value in widget.field_options:
                                widget.field_value = value
                        
                        total_filled += 1
                        self.logger.debug(f"Filled field '{field_name}' with value: {value}")
            
            if total_filled > 0:
                document.mark_modified()
                self.logger.info(f"Successfully filled {total_filled} form fields")
                return OperationResult.SUCCESS
            else:
                self.logger.warning("No matching form fields found")
                return OperationResult.SUCCESS
                
        except Exception as e:
            self.logger.error(f"Failed to fill form fields: {e}")
            return OperationResult.FAILED


class ValidateFormOperation(FormOperation):
    """Operation to validate form field data."""
    
    def __init__(self, validation_rules: Dict[str, Dict[str, Any]]):
        super().__init__(OperationType.VALIDATE_FORM)
        
        self.set_parameter("validation_rules", validation_rules)
    
    def validate(self, document: PDFDocument) -> bool:
        """Validate form validation parameters."""
        if not super().validate(document):
            return False
        
        validation_rules = self.get_parameter("validation_rules")
        
        if not validation_rules or not isinstance(validation_rules, dict):
            self.logger.error("Validation rules must be a non-empty dictionary")
            return False
        
        return True
    
    def execute(self, document: PDFDocument) -> OperationResult:
        """Execute form validation."""
        try:
            validation_rules = self.get_parameter("validation_rules")
            validation_errors = []
            
            for page_idx in range(document.page_count):
                page = document.get_page(page_idx)
                widgets = page.widgets()
                
                for widget in widgets:
                    field_name = widget.field_name
                    
                    if field_name in validation_rules:
                        rules = validation_rules[field_name]
                        errors = self._validate_field(widget, rules)
                        if errors:
                            validation_errors.extend([f"Page {page_idx + 1}, {field_name}: {err}" for err in errors])
            
            if validation_errors:
                self.logger.error(f"Form validation failed with {len(validation_errors)} errors")
                for error in validation_errors:
                    self.logger.error(f"  - {error}")
                return OperationResult.FAILED
            else:
                self.logger.info("Form validation passed successfully")
                return OperationResult.SUCCESS
                
        except Exception as e:
            self.logger.error(f"Failed to validate form: {e}")
            return OperationResult.FAILED
    
    def _validate_field(self, widget, rules):
        """Validate a single form field."""
        errors = []
        field_value = widget.field_value
        
        # Required field validation
        if rules.get("required", False) and not field_value:
            errors.append("Field is required")
        
        # Type validation
        expected_type = rules.get("type")
        if expected_type and field_value:
            if expected_type == "email" and "@" not in str(field_value):
                errors.append("Invalid email format")
            elif expected_type == "number" and not str(field_value).replace(".", "").replace("-", "").isdigit():
                errors.append("Must be a number")
            elif expected_type == "date":
                try:
                    datetime.strptime(str(field_value), rules.get("date_format", "%Y-%m-%d"))
                except ValueError:
                    errors.append("Invalid date format")
        
        # Length validation
        min_length = rules.get("min_length")
        max_length = rules.get("max_length")
        if field_value and isinstance(field_value, str):
            if min_length and len(field_value) < min_length:
                errors.append(f"Minimum length is {min_length} characters")
            if max_length and len(field_value) > max_length:
                errors.append(f"Maximum length is {max_length} characters")
        
        # Pattern validation
        pattern = rules.get("pattern")
        if pattern and field_value:
            import re
            if not re.match(pattern, str(field_value)):
                errors.append("Value does not match required pattern")
        
        return errors


class ExportFormDataOperation(FormOperation):
    """Operation to export form data to various formats."""
    
    def __init__(self, output_path: str, format_type: str = "json", 
                 include_empty: bool = False):
        super().__init__(OperationType.EXPORT_FORM_DATA)
        
        self.set_parameter("output_path", output_path)
        self.set_parameter("format_type", format_type)
        self.set_parameter("include_empty", include_empty)
    
    def validate(self, document: PDFDocument) -> bool:
        """Validate form data export parameters."""
        if not super().validate(document):
            return False
        
        output_path = self.get_parameter("output_path")
        format_type = self.get_parameter("format_type")
        include_empty = self.get_parameter("include_empty")
        
        if not output_path or not isinstance(output_path, str):
            self.logger.error("Output path must be a non-empty string")
            return False
        
        valid_formats = ["json", "csv", "xml", "fdf"]
        if format_type not in valid_formats:
            self.logger.error(f"Invalid format type: {format_type}. Must be one of {valid_formats}")
            return False
        
        if not isinstance(include_empty, bool):
            self.logger.error("include_empty must be a boolean")
            return False
        
        return True
    
    def execute(self, document: PDFDocument) -> OperationResult:
        """Execute form data export."""
        try:
            output_path = self.get_parameter("output_path")
            format_type = self.get_parameter("format_type")
            include_empty = self.get_parameter("include_empty")
            
            form_data = self._extract_form_data(document, include_empty)
            
            if format_type == "json":
                self._export_json(form_data, output_path)
            elif format_type == "csv":
                self._export_csv(form_data, output_path)
            elif format_type == "xml":
                self._export_xml(form_data, output_path)
            elif format_type == "fdf":
                self._export_fdf(form_data, output_path)
            
            self.logger.info(f"Form data exported to {output_path} in {format_type} format")
            return OperationResult.SUCCESS
            
        except Exception as e:
            self.logger.error(f"Failed to export form data: {e}")
            return OperationResult.FAILED
    
    def _extract_form_data(self, document, include_empty):
        """Extract form data from all pages."""
        form_data = {}
        
        for page_idx in range(document.page_count):
            page = document.get_page(page_idx)
            widgets = page.widgets()
            
            for widget in widgets:
                field_name = widget.field_name
                field_value = widget.field_value
                
                if field_value or include_empty:
                    form_data[field_name] = {
                        "value": field_value or "",
                        "type": self._get_field_type_name(widget.field_type),
                        "page": page_idx + 1
                    }
        
        return form_data
    
    def _get_field_type_name(self, field_type):
        """Get readable field type name."""
        type_mapping = {
            fitz.PDF_WIDGET_TYPE_TEXT: "text",
            fitz.PDF_WIDGET_TYPE_CHECKBOX: "checkbox",
            fitz.PDF_WIDGET_TYPE_RADIOBUTTON: "radio",
            fitz.PDF_WIDGET_TYPE_LISTBOX: "list",
            fitz.PDF_WIDGET_TYPE_COMBOBOX: "dropdown",
            fitz.PDF_WIDGET_TYPE_SIGNATURE: "signature"
        }
        return type_mapping.get(field_type, "unknown")
    
    def _export_json(self, form_data, output_path):
        """Export form data as JSON."""
        import json
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(form_data, f, indent=2, ensure_ascii=False)
    
    def _export_csv(self, form_data, output_path):
        """Export form data as CSV."""
        import csv
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Field Name", "Value", "Type", "Page"])
            for field_name, data in form_data.items():
                writer.writerow([field_name, data["value"], data["type"], data["page"]])
    
    def _export_xml(self, form_data, output_path):
        """Export form data as XML."""
        from xml.etree.ElementTree import Element, SubElement, ElementTree
        
        root = Element("form_data")
        for field_name, data in form_data.items():
            field_elem = SubElement(root, "field", name=field_name)
            field_elem.set("type", data["type"])
            field_elem.set("page", str(data["page"]))
            field_elem.text = data["value"]
        
        tree = ElementTree(root)
        tree.write(output_path, encoding='utf-8', xml_declaration=True)
    
    def _export_fdf(self, form_data, output_path):
        """Export form data as FDF (Forms Data Format)."""
        # Basic FDF implementation
        fdf_content = """%FDF-1.2
%âãÏÓ
1 0 obj
<<
/FDF
<<
/Fields [
"""
        
        for field_name, data in form_data.items():
            if data["value"]:
                fdf_content += f'''<< /V ({data["value"]}) /T ({field_name}) >>
'''
        
        fdf_content += """]
>>
endobj
trailer
<<
/Root 1 0 R
>>
%%EOF"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(fdf_content)