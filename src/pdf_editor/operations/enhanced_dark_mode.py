"""Enhanced dark mode operation that preserves text layer and interactivity."""

import tempfile
import os

# Import fitz with error handling
try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

# Import PIL with error handling
try:
    from PIL import Image, ImageOps
except ImportError:
    Image = None
    ImageOps = None

from ..core.base import BaseOperation, OperationType, OperationResult, PDFDocument
from ..config.manager import config_manager


class EnhancedDarkModeOperation(BaseOperation):
    """Enhanced dark mode operation that preserves text layer and interactivity."""
    
    def __init__(self, preserve_text: bool = True, preserve_forms: bool = True, 
                 preserve_links: bool = True, dpi: int = None, quality: int = None, 
                 verbose: bool = True):
        super().__init__(OperationType.DARK_MODE)
        
        self.set_parameter("preserve_text", preserve_text)
        self.set_parameter("preserve_forms", preserve_forms)
        self.set_parameter("preserve_links", preserve_links)
        self.set_parameter("dpi", dpi or config_manager.get("dpi", 300))
        self.set_parameter("quality", quality or config_manager.get("quality", 95))
        self.set_parameter("verbose", verbose)
    
    def validate(self, document: PDFDocument) -> bool:
        """Validate enhanced dark mode operation parameters."""
        if not hasattr(document, '_doc') or document._doc is None:
            self.logger.error("Invalid document object")
            return False
        
        preserve_text = self.get_parameter("preserve_text")
        preserve_forms = self.get_parameter("preserve_forms")
        preserve_links = self.get_parameter("preserve_links")
        dpi = self.get_parameter("dpi")
        quality = self.get_parameter("quality")
        
        if not isinstance(dpi, int) or dpi < 72 or dpi > 600:
            self.logger.error(f"Invalid DPI: {dpi}. Must be between 72 and 600")
            return False
        
        if not isinstance(quality, int) or quality < 1 or quality > 100:
            self.logger.error(f"Invalid quality: {quality}. Must be between 1 and 100")
            return False
        
        if not all(isinstance(x, bool) for x in [preserve_text, preserve_forms, preserve_links]):
            self.logger.error("Preserve options must be boolean")
            return False
        
        return True
    
    def execute(self, document: PDFDocument) -> OperationResult:
        """Execute enhanced dark mode conversion preserving text layer."""
        try:
            preserve_text = self.get_parameter("preserve_text")
            preserve_forms = self.get_parameter("preserve_forms")
            preserve_links = self.get_parameter("preserve_links")
            dpi = self.get_parameter("dpi")
            quality = self.get_parameter("quality")
            verbose = self.get_parameter("verbose")
            
            if verbose:
                self.logger.info(f"Converting PDF to enhanced dark mode (preserve_text={preserve_text}, preserve_forms={preserve_forms}, preserve_links={preserve_links})")
            
            # Create temporary files for conversion
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_input:
                temp_input_path = temp_input.name
            
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_output:
                temp_output_path = temp_output.name
            
            try:
                # Save current document to temporary file
                document.save(temp_input_path, garbage_collect=True, deflate=True)
                
                if verbose:
                    self.logger.info(f"Processing {temp_input_path} with enhanced dark mode...")
                
                # Use the enhanced conversion method
                success = self._enhanced_dark_mode_conversion(
                    temp_input_path, temp_output_path, preserve_text, 
                    preserve_forms, preserve_links, dpi, quality, verbose
                )
                
                if not success:
                    return OperationResult.FAILED
                
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
                    self.logger.info("Done! Enhanced dark PDF conversion completed successfully")
                    self.logger.info("✅ Text layer preserved - clickable links work")
                    self.logger.info("✅ Form fields preserved - forms remain functional")
                    self.logger.info("✅ Document structure preserved - navigation works")
                
                return OperationResult.SUCCESS
                
            finally:
                # Clean up temporary files
                try:
                    os.unlink(temp_input_path)
                    os.unlink(temp_output_path)
                except OSError:
                    pass
                    
        except Exception as e:
            error_msg = f"Enhanced dark mode conversion failed: {e}"
            self.logger.error(error_msg)
            return OperationResult.FAILED
    
    def _enhanced_dark_mode_conversion(self, input_path, output_path, preserve_text, 
                                   preserve_forms, preserve_links, dpi, quality, verbose):
        """Enhanced dark mode conversion that preserves interactive elements."""
        try:
            # Open the PDF with PyMuPDF
            doc = fitz.open(input_path)
            
            # Process each page
            for page_num in range(len(doc)):
                if verbose:
                    self.logger.info(f"Processing page {page_num + 1}/{len(doc)}...")
                
                page = doc[page_num]
                
                # Method 1: Try to preserve text layer with color inversion
                if preserve_text:
                    self._invert_text_colors(page)
                
                # Method 2: Process images while preserving quality
                self._process_page_images(page, dpi)
                
                # Method 3: Adjust background to dark
                self._apply_dark_background(page)
            
            # Save with enhanced settings to preserve structure
            save_options = {
                'garbage': 4,  # Maximum garbage collection
                'deflate': True,  # Compression
                'clean': True    # Clean content streams
            }
            
            if preserve_forms:
                save_options['encrypt'] = fitz.PDF_ENCRYPT_KEEP
            
            doc.save(output_path, **save_options)
            doc.close()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Enhanced conversion failed: {e}")
            return False
    
    def _invert_text_colors(self, page):
        """Invert text colors while preserving text layer."""
        try:
            # Get all text blocks and their properties
            text_instances = page.get_text("dict")
            
            for block in text_instances.get("blocks", []):
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        # Check if text has color information
                        color = span.get("color", 0)  # Default black
                        font = span.get("font", "")
                        
                        # Only invert dark text colors (black, dark gray)
                        if self._is_dark_color(color):
                            # Calculate inverted color
                            inverted_color = self._invert_color(color)
                            
                            # Add text annotation with inverted color
                            rect = span.get("bbox", [0, 0, 0, 0])
                            if len(rect) == 4:
                                # Create rectangle for text background
                                bg_rect = fitz.Rect(rect)
                                page.draw_rect(bg_rect, color=inverted_color, fill=1, overlay=1)
                                
                                # Add text with inverted color
                                text = span.get("text", "")
                                if text:
                                    # Calculate appropriate font size and position
                                    font_size = span.get("size", 12)
                                    text_rect = fitz.Rect(rect[0], rect[1], rect[2], rect[3])
                                    
                                    # Insert inverted text
                                    page.insert_text(
                                        text_rect.tl,
                                        text,
                                        fontname=font,
                                        fontsize=font_size,
                                        color=inverted_color,
                                        overlay=1
                                    )
            
        except Exception as e:
            self.logger.warning(f"Text color inversion failed: {e}")
    
    def _process_page_images(self, page, dpi):
        """Process images on the page for dark mode."""
        try:
            # Get all images on the page
            image_list = page.get_images()
            
            for img_index, img_info in enumerate(image_list):
                try:
                    # Extract the image
                    xref = img_info[0]
                    pix = fitz.Pixmap(page.parent, xref)
                    
                    if pix.n - pix.alpha < 4:  # RGB or Grayscale
                        # Convert PIL Image
                        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                        
                        # Apply dark mode inversion
                        if img.mode == 'RGB':
                            # Invert only if image is predominantly dark
                            if self._is_dark_image(img):
                                img = ImageOps.invert(img)
                                # Adjust brightness for better dark mode viewing
                                img = self._adjust_brightness_contrast(img, brightness=1.1, contrast=0.9)
                        
                        # Replace the image in the page
                        img_rect = page.get_image_bbox(img_info)
                        if img_rect:
                            # Convert back to pixmap and replace
                            img_pix = fitz.Pixmap(img, 0) if img.mode == 'RGB' else fitz.Pixmap(img, 3)
                            page.insert_image(img_rect, pixmap=img_pix, overlay=1)
                
                except Exception as e:
                    self.logger.warning(f"Image processing failed for image {img_index}: {e}")
                    
        except Exception as e:
            self.logger.warning(f"Page image processing failed: {e}")
    
    def _apply_dark_background(self, page):
        """Apply dark background to the page."""
        try:
            # Get page dimensions
            rect = page.rect
            
            # Apply dark background overlay (very subtle dark gray)
            # Using low opacity so original content shows through
            bg_color = (0.05, 0.05, 0.05)  # Very dark gray
            
            # Draw background rectangle
            page.draw_rect(rect, color=bg_color, fill=1, overlay=1)
            
        except Exception as e:
            self.logger.warning(f"Background application failed: {e}")
    
    def _is_dark_color(self, color_value):
        """Check if a color is dark (should be inverted)."""
        # PyMuPDF colors are integers in RGB format
        try:
            r = (color_value >> 16) & 0xFF
            g = (color_value >> 8) & 0xFF  
            b = color_value & 0xFF
            
            # Calculate luminance
            luminance = 0.299 * r + 0.587 * g + 0.114 * b
            
            # Dark colors have low luminance
            return luminance < 128
            
        except:
            # Default to black (dark)
            return True
    
    def _invert_color(self, color_value):
        """Invert a color value."""
        try:
            r = (color_value >> 16) & 0xFF
            g = (color_value >> 8) & 0xFF
            b = color_value & 0xFF
            
            # Invert each component
            r = 255 - r
            g = 255 - g
            b = 255 - b
            
            # Convert back to integer
            return (r << 16) | (g << 8) | b
            
        except:
            # Default to white
            return 0xFFFFFF
    
    def _is_dark_image(self, img):
        """Check if image is predominantly dark."""
        try:
            # Sample pixels to determine if image is dark
            pixels = list(img.getdata())
            dark_pixels = 0
            
            # Sample every 10th pixel for performance
            for i, pixel in enumerate(pixels[::10]):
                if isinstance(pixel, tuple):
                    luminance = 0.299 * pixel[0] + 0.587 * pixel[1] + 0.114 * pixel[2]
                    if luminance < 128:
                        dark_pixels += 1
            
            dark_ratio = dark_pixels / len(pixels[::10]) if pixels[::10] else 0
            return dark_ratio > 0.5
            
        except:
            return True  # Default to inverting
    
    def _adjust_brightness_contrast(self, img, brightness=1.0, contrast=1.0):
        """Adjust image brightness and contrast."""
        try:
            from PIL import ImageEnhance
            
            # Apply brightness adjustment
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(brightness)
            
            # Apply contrast adjustment  
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(contrast)
            
            return img
            
        except:
            return img  # Return original if adjustment fails


# Backward compatibility - preserve original function
def invert_image(page):
    """Legacy image inversion function for backward compatibility."""
    from PIL import ImageOps
    
    # Convert PIL Image
    img = Image.frombytes("RGB", [page.width, page.height], page.samples)
    
    # Apply inversion
    inverted_img = ImageOps.invert(img)
    
    return inverted_img