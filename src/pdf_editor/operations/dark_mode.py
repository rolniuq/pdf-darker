"""Dark mode operation using proven conversion logic from original init.py."""

from typing import Any, Dict, Union
from pathlib import Path
import tempfile
import os

from ..core.base import BaseOperation, OperationType, OperationResult, PDFDocument, PDFException
from ..config.manager import config_manager
from ..utils.logging import get_logger


# Import the proven dark mode conversion functions
from .dark_mode_legacy import invert_image


class DarkModeOperation(BaseOperation):
    """Operation to convert PDF to dark mode using proven logic."""
    
    def __init__(self, dpi: int = None, quality: int = None, verbose: bool = True):
        # Use the DARK_MODE operation type
        super().__init__(OperationType.DARK_MODE)
        
        # Set parameters from config or defaults (matching original init.py)
        self.set_parameter("dpi", dpi or config_manager.get("dpi", 300))
        self.set_parameter("quality", quality or config_manager.get("quality", 95))
        self.set_parameter("verbose", verbose)
    
    def validate(self, document: PDFDocument) -> bool:
        """Validate dark mode operation parameters."""
        if not hasattr(document, '_doc') or document._doc is None:
            self.logger.error("Invalid document object")
            return False
        
        dpi = self.get_parameter("dpi")
        quality = self.get_parameter("quality")
        
        if not isinstance(dpi, int) or dpi < 72 or dpi > 600:
            self.logger.error(f"Invalid DPI: {dpi}. Must be between 72 and 600")
            return False
        
        if not isinstance(quality, int) or quality < 1 or quality > 100:
            self.logger.error(f"Invalid quality: {quality}. Must be between 1 and 100")
            return False
        
        return True
    
    def execute(self, document: PDFDocument) -> OperationResult:
        """Execute dark mode conversion using proven algorithm."""
        try:
            from pdf2image import convert_from_path
            
            dpi = self.get_parameter("dpi")
            quality = self.get_parameter("quality")
            verbose = self.get_parameter("verbose")
            
            if verbose:
                self.logger.info(f"Converting PDF to dark mode (DPI={dpi}, quality={quality})")
            
            # Create temporary files for conversion
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_input:
                temp_input_path = temp_input.name
            
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_output:
                temp_output_path = temp_output.name
            
            try:
                # Save current document to temporary file
                document.save(temp_input_path, garbage_collect=True, deflate=True)
                
                # Use the proven conversion logic from original init.py
                if verbose:
                    self.logger.info(f"Converting {temp_input_path} to dark mode...")
                
                # Convert PDF pages to images (higher DPI = sharper text)
                pages = convert_from_path(temp_input_path, dpi=dpi)
                
                # Invert colors for each page using proven function
                inverted_pages = []
                for i, page in enumerate(pages):
                    if verbose:
                        self.logger.info(f"Processing page {i + 1}/{len(pages)}...")
                    
                    # Use the proven invert_image function from original code
                    inverted = invert_image(page)
                    inverted_pages.append(inverted)
                
                # Save as PDF using proven method
                if verbose:
                    self.logger.info("Saving dark mode PDF...")
                
                inverted_pages[0].save(
                    temp_output_path,
                    save_all=True,
                    append_images=inverted_pages[1:],
                    quality=quality
                )
                
                # Load the converted document back
                from .document import PDFDocument as DocumentImpl
                temp_doc = DocumentImpl(temp_output_path)
                
                # Replace the current document content with the dark mode version
                document._doc.close()
                document._doc = temp_doc._doc
                document._pages = temp_doc._pages
                document._metadata = temp_doc._metadata
                
                # Prevent temp_doc from closing the document when it's garbage collected
                temp_doc._doc = None
                
                document.mark_modified()
                
                if verbose:
                    self.logger.info("Done! Dark PDF conversion completed successfully")
                
                return OperationResult.SUCCESS
                
            finally:
                # Clean up temporary files
                try:
                    os.unlink(temp_input_path)
                    os.unlink(temp_output_path)
                except OSError:
                    pass
                    
        except ImportError as e:
            error_msg = f"Missing required dependencies for dark mode conversion: {e}"
            self.logger.error(error_msg)
            return OperationResult.FAILED
        except Exception as e:
            error_msg = f"Dark mode conversion failed: {e}"
            self.logger.error(error_msg)
            return OperationResult.FAILED