"""Security and metadata operations for PDF editing."""

from typing import Dict, List, Tuple
import fitz  # PyMuPDF
import os
import tempfile
from datetime import datetime

from ..core.base import BaseOperation, OperationType, OperationResult, PDFDocument


class SecurityOperation(BaseOperation):
    """Base class for security operations."""
    
    def __init__(self, operation_type: OperationType):
        super().__init__(operation_type)


class SetPasswordOperation(SecurityOperation):
    """Operation to set password protection for PDF."""
    
    def __init__(self, user_password: str = None, owner_password: str = None,
                 permissions: Dict[str, bool] = None, encryption_strength: int = 128):
        super().__init__(OperationType.SET_PASSWORD)
        
        self.set_parameter("user_password", user_password)
        self.set_parameter("owner_password", owner_password)
        self.set_parameter("permissions", permissions or {})
        self.set_parameter("encryption_strength", encryption_strength)
    
    def validate(self, document: PDFDocument) -> bool:
        """Validate password protection parameters."""
        if not super().validate(document):
            return False
        
        user_password = self.get_parameter("user_password")
        owner_password = self.get_parameter("owner_password")
        permissions = self.get_parameter("permissions")
        encryption_strength = self.get_parameter("encryption_strength")
        
        # Validate passwords
        if not user_password and not owner_password:
            self.logger.error("At least one password (user or owner) must be provided")
            return False
        
        if user_password and len(user_password) < 4:
            self.logger.error("User password must be at least 4 characters long")
            return False
        
        if owner_password and len(owner_password) < 4:
            self.logger.error("Owner password must be at least 4 characters long")
            return False
        
        # Validate permissions
        valid_permissions = [
            "print", "modify", "copy", "annotate", "fill_forms", 
            "extract", "assemble", "print_high"
        ]
        
        if permissions:
            for perm in permissions:
                if perm not in valid_permissions:
                    self.logger.error(f"Invalid permission: {perm}. Must be one of {valid_permissions}")
                    return False
        
        # Validate encryption strength
        if encryption_strength not in [40, 128, 256]:
            self.logger.error("Encryption strength must be 40, 128, or 256")
            return False
        
        return True
    
    def execute(self, document: PDFDocument) -> OperationResult:
        """Execute password protection setup."""
        try:
            user_password = self.get_parameter("user_password")
            owner_password = self.get_parameter("owner_password")
            permissions = self.get_parameter("permissions")
            encryption_strength = self.get_parameter("encryption_strength")
            
            # Convert permissions to PyMuPDF format
            perm_flags = self._convert_permissions(permissions)
            
            # Save current document with password protection
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
                temp_path = temp_file.name
            
            try:
                # Set encryption permissions
                if user_password:
                    document._doc.save(
                        temp_path,
                        encryption=fitz.PDF_ENCRYPT_AES_256 if encryption_strength == 256 else fitz.PDF_ENCRYPT_KEEP,
                        user_pw=user_password,
                        owner_pw=owner_password,
                        permissions=perm_flags
                    )
                else:
                    document._doc.save(
                        temp_path,
                        encryption=fitz.PDF_ENCRYPT_AES_256 if encryption_strength == 256 else fitz.PDF_ENCRYPT_KEEP,
                        owner_pw=owner_password,
                        permissions=perm_flags
                    )
                
                # Reopen the protected document
                protected_doc = fitz.open(temp_path)
                
                # Replace current document with protected version
                document._doc.close()
                document._doc = protected_doc
                document.mark_modified()
                
                self.logger.info(f"PDF password protection set with {encryption_strength}-bit encryption")
                return OperationResult.SUCCESS
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
        except Exception as e:
            self.logger.error(f"Failed to set password protection: {e}")
            return OperationResult.FAILED
    
    def _convert_permissions(self, permissions: Dict[str, bool]) -> int:
        """Convert permission dictionary to PyMuPDF permission flags."""
        perm = fitz.PDF_PERM_ACCESSIBILITY  # Always allow accessibility
        
        if permissions.get("print", True):
            perm |= fitz.PDF_PERM_PRINT
        
        if permissions.get("modify", True):
            perm |= fitz.PDF_PERM_MODIFY
        
        if permissions.get("copy", True):
            perm |= fitz.PDF_PERM_COPY
        
        if permissions.get("annotate", True):
            perm |= fitz.PDF_PERM_ANNOTATE
        
        if permissions.get("fill_forms", True):
            perm |= fitz.PDF_PERM_FORM
        
        if permissions.get("extract", True):
            perm |= fitz.PDF_PERM_EXTRACT
        
        if permissions.get("assemble", True):
            perm |= fitz.PDF_PERM_ASSEMBLE
        
        if permissions.get("print_high", True):
            perm |= fitz.PDF_PERM_PRINT_HQ
        
        return perm


class AddSignatureOperation(SecurityOperation):
    """Operation to add digital signatures to PDF."""
    
    def __init__(self, page_number: int, rect: tuple, signature_image: str,
                 signer_name: str = None, reason: str = None, location: str = None):
        super().__init__(OperationType.ADD_SIGNATURE)
        
        self.set_parameter("page_number", page_number)
        self.set_parameter("rect", rect)
        self.set_parameter("signature_image", signature_image)
        self.set_parameter("signer_name", signer_name)
        self.set_parameter("reason", reason)
        self.set_parameter("location", location)
    
    def validate(self, document: PDFDocument) -> bool:
        """Validate digital signature parameters."""
        if not super().validate(document):
            return False
        
        page_number = self.get_parameter("page_number")
        rect = self.get_parameter("rect")
        signature_image = self.get_parameter("signature_image")
        
        # Validate page number
        if not isinstance(page_number, int) or page_number < 0 or page_number >= document.page_count:
            self.logger.error(f"Invalid page number: {page_number}")
            return False
        
        # Validate rectangle
        if (not isinstance(rect, tuple) or len(rect) != 4 or 
            not all(isinstance(x, (int, float)) for x in rect)):
            self.logger.error("Rect must be a tuple of 4 numbers (x0, y0, x1, y1)")
            return False
        
        # Validate signature image
        if not signature_image or not os.path.exists(signature_image):
            self.logger.error(f"Signature image file not found: {signature_image}")
            return False
        
        return True
    
    def execute(self, document: PDFDocument) -> OperationResult:
        """Execute digital signature addition."""
        try:
            page_number = self.get_parameter("page_number")
            rect = self.get_parameter("rect")
            signature_image = self.get_parameter("signature_image")
            signer_name = self.get_parameter("signer_name")
            reason = self.get_parameter("reason")
            location = self.get_parameter("location")
            
            page = document.get_page(page_number)
            
            # Insert signature image
            img_rect = fitz.Rect(rect)
            page.insert_image(img_rect, filename=signature_image)
            
            # Add signature annotation
            signature_text = f"Digitally signed by {signer_name or 'Unknown'}"
            if reason:
                signature_text += f"\\nReason: {reason}"
            if location:
                signature_text += f"\\nLocation: {location}"
            signature_text += f"\\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # Create a text annotation below the signature
            text_rect = (rect[0], rect[3] + 10, rect[2], rect[3] + 50)
            annot = page.add_text_annot(text_rect, signature_text)
            annot.set_icon("Key")
            annot.set_colors(stroke=(0, 0, 1))  # Blue color
            
            document.mark_modified()
            self.logger.info(f"Digital signature added on page {page_number}")
            
            return OperationResult.SUCCESS
            
        except Exception as e:
            self.logger.error(f"Failed to add digital signature: {e}")
            return OperationResult.FAILED


class EditMetadataOperation(SecurityOperation):
    """Operation to edit PDF metadata."""
    
    def __init__(self, metadata: Dict[str, str]):
        super().__init__(OperationType.EDIT_METADATA)
        
        self.set_parameter("metadata", metadata)
    
    def validate(self, document: PDFDocument) -> bool:
        """Validate metadata parameters."""
        if not super().validate(document):
            return False
        
        metadata = self.get_parameter("metadata")
        
        if not metadata or not isinstance(metadata, dict):
            self.logger.error("Metadata must be a non-empty dictionary")
            return False
        
        # Validate metadata keys
        valid_keys = [
            "title", "author", "subject", "keywords", "creator", 
            "producer", "creation_date", "modification_date"
        ]
        
        for key in metadata.keys():
            if key not in valid_keys:
                self.logger.warning(f"Unknown metadata key: {key}. Valid keys are: {valid_keys}")
        
        return True
    
    def execute(self, document: PDFDocument) -> OperationResult:
        """Execute metadata editing."""
        try:
            metadata = self.get_parameter("metadata")
            
            # Set metadata using PyMuPDF
            doc_meta = document._doc.metadata
            
            for key, value in metadata.items():
                if key == "title":
                    doc_meta["title"] = value
                elif key == "author":
                    doc_meta["author"] = value
                elif key == "subject":
                    doc_meta["subject"] = value
                elif key == "keywords":
                    doc_meta["keywords"] = value
                elif key == "creator":
                    doc_meta["creator"] = value
                elif key == "producer":
                    doc_meta["producer"] = value
                elif key == "creation_date":
                    doc_meta["creationDate"] = value
                elif key == "modification_date":
                    doc_meta["modDate"] = value
            
            # Update document metadata
            document._doc.set_metadata(doc_meta)
            document.mark_modified()
            
            self.logger.info(f"Updated PDF metadata: {list(metadata.keys())}")
            return OperationResult.SUCCESS
            
        except Exception as e:
            self.logger.error(f"Failed to edit metadata: {e}")
            return OperationResult.FAILED


class AddSecurityWatermarkOperation(SecurityOperation):
    """Operation to add security watermarks to PDF."""
    
    def __init__(self, watermark_text: str, page_numbers: List[int] = None,
                 opacity: float = 0.3, rotation: float = 45, 
                 color: Tuple[float, float, float] = (0.5, 0.5, 0.5),
                 font_size: int = 48, position: str = "center"):
        super().__init__(OperationType.ADD_SECURITY_WATERMARK)
        
        self.set_parameter("watermark_text", watermark_text)
        self.set_parameter("page_numbers", page_numbers or [])
        self.set_parameter("opacity", opacity)
        self.set_parameter("rotation", rotation)
        self.set_parameter("color", color)
        self.set_parameter("font_size", font_size)
        self.set_parameter("position", position)
    
    def validate(self, document: PDFDocument) -> bool:
        """Validate security watermark parameters."""
        if not super().validate(document):
            return False
        
        watermark_text = self.get_parameter("watermark_text")
        page_numbers = self.get_parameter("page_numbers")
        opacity = self.get_parameter("opacity")
        rotation = self.get_parameter("rotation")
        color = self.get_parameter("color")
        font_size = self.get_parameter("font_size")
        position = self.get_parameter("position")
        
        # Validate watermark text
        if not watermark_text or not isinstance(watermark_text, str):
            self.logger.error("Watermark text must be a non-empty string")
            return False
        
        # Validate page numbers
        if page_numbers:
            for page_num in page_numbers:
                if not isinstance(page_num, int) or page_num < 0 or page_num >= document.page_count:
                    self.logger.error(f"Invalid page number: {page_num}")
                    return False
        
        # Validate opacity
        if not isinstance(opacity, (int, float)) or opacity < 0 or opacity > 1:
            self.logger.error("Opacity must be a number between 0 and 1")
            return False
        
        # Validate rotation
        if not isinstance(rotation, (int, float)):
            self.logger.error("Rotation must be a number")
            return False
        
        # Validate color
        if (not isinstance(color, tuple) or len(color) != 3 or
            not all(isinstance(c, (int, float)) and 0 <= c <= 1 for c in color)):
            self.logger.error("Color must be a tuple of 3 values between 0 and 1")
            return False
        
        # Validate font size
        if not isinstance(font_size, int) or font_size <= 0:
            self.logger.error("Font size must be a positive integer")
            return False
        
        # Validate position
        valid_positions = ["center", "top_left", "top_right", "bottom_left", "bottom_right"]
        if position not in valid_positions:
            self.logger.error(f"Invalid position: {position}. Must be one of {valid_positions}")
            return False
        
        return True
    
    def execute(self, document: PDFDocument) -> OperationResult:
        """Execute security watermark addition."""
        try:
            watermark_text = self.get_parameter("watermark_text")
            page_numbers = self.get_parameter("page_numbers")
            opacity = self.get_parameter("opacity")
            rotation = self.get_parameter("rotation")
            color = self.get_parameter("color")
            font_size = self.get_parameter("font_size")
            position = self.get_parameter("position")
            
            pages_to_process = page_numbers if page_numbers else list(range(document.page_count))
            total_watermarked = 0
            
            for page_num in pages_to_process:
                page = document.get_page(page_num)
                
                # Calculate watermark position
                page_rect = page.rect
                if position == "center":
                    center_x = page_rect.width / 2
                    center_y = page_rect.height / 2
                elif position == "top_left":
                    center_x = page_rect.width / 4
                    center_y = page_rect.height / 4
                elif position == "top_right":
                    center_x = 3 * page_rect.width / 4
                    center_y = page_rect.height / 4
                elif position == "bottom_left":
                    center_x = page_rect.width / 4
                    center_y = 3 * page_rect.height / 4
                elif position == "bottom_right":
                    center_x = 3 * page_rect.width / 4
                    center_y = 3 * page_rect.height / 4
                
                # Create watermark text with rotation
                text_point = fitz.Point(center_x, center_y)
                text_rect = fitz.Rect(
                    center_x - 200, center_y - 50,
                    center_x + 200, center_y + 50
                )
                
                # Add watermark as text annotation with transparency
                annot = page.add_freetext_annot(text_rect, watermark_text, 
                    fontsize=font_size,
                    rotate=rotation,
                    color=color,
                    fill_color=(*color, opacity),
                    overlay=True
                )
                
                # Set watermark properties
                annot.set_flags(fitz.PDF_ANNOT_INVISIBLE | fitz.PDF_ANNOT_PRINT)
                
                total_watermarked += 1
            
            if total_watermarked > 0:
                document.mark_modified()
                self.logger.info(f"Added security watermark to {total_watermarked} pages")
                return OperationResult.SUCCESS
            else:
                self.logger.warning("No pages were watermarked")
                return OperationResult.FAILED
                
        except Exception as e:
            self.logger.error(f"Failed to add security watermark: {e}")
            return OperationResult.FAILED


class ExportMetadataOperation(SecurityOperation):
    """Operation to export PDF metadata to various formats."""
    
    def __init__(self, output_path: str, format_type: str = "json"):
        super().__init__(OperationType.EXPORT_FORM_DATA)  # Reuse existing type
        
        self.set_parameter("output_path", output_path)
        self.set_parameter("format_type", format_type)
    
    def validate(self, document: PDFDocument) -> bool:
        """Validate metadata export parameters."""
        if not super().validate(document):
            return False
        
        output_path = self.get_parameter("output_path")
        format_type = self.get_parameter("format_type")
        
        if not output_path or not isinstance(output_path, str):
            self.logger.error("Output path must be a non-empty string")
            return False
        
        valid_formats = ["json", "xml", "txt"]
        if format_type not in valid_formats:
            self.logger.error(f"Invalid format type: {format_type}. Must be one of {valid_formats}")
            return False
        
        return True
    
    def execute(self, document: PDFDocument) -> OperationResult:
        """Execute metadata export."""
        try:
            output_path = self.get_parameter("output_path")
            format_type = self.get_parameter("format_type")
            
            # Extract metadata
            metadata = document._doc.metadata
            
            if format_type == "json":
                self._export_json_metadata(metadata, output_path)
            elif format_type == "xml":
                self._export_xml_metadata(metadata, output_path)
            elif format_type == "txt":
                self._export_txt_metadata(metadata, output_path)
            
            self.logger.info(f"Metadata exported to {output_path} in {format_type} format")
            return OperationResult.SUCCESS
            
        except Exception as e:
            self.logger.error(f"Failed to export metadata: {e}")
            return OperationResult.FAILED
    
    def _export_json_metadata(self, metadata, output_path):
        """Export metadata as JSON."""
        import json
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False, default=str)
    
    def _export_xml_metadata(self, metadata, output_path):
        """Export metadata as XML."""
        from xml.etree.ElementTree import Element, SubElement, ElementTree
        
        root = Element("metadata")
        for key, value in metadata.items():
            elem = SubElement(root, key)
            elem.text = str(value) if value else ""
        
        tree = ElementTree(root)
        tree.write(output_path, encoding='utf-8', xml_declaration=True)
    
    def _export_txt_metadata(self, metadata, output_path):
        """Export metadata as plain text."""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("PDF Metadata\\n")
            f.write("=" * 40 + "\\n\\n")
            for key, value in metadata.items():
                f.write(f"{key.title()}: {value if value else '(empty)'}\\n")