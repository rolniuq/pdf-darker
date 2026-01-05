"""PDF document implementation using PyMuPDF (fitz)."""

import fitz  # PyMuPDF
from typing import List, Dict, Any, Optional, Union, Tuple
from pathlib import Path
from datetime import datetime

from .base import PDFDocument as BasePDFDocument, PDFException
from ..utils.logging import get_logger
from ..config.manager import config_manager


class PDFPage:
    """Represents a single PDF page."""
    
    def __init__(self, page: fitz.Page):
        """Initialize PDF page.
        
        Args:
            page: PyMuPDF page object
        """
        self._page = page
        self.logger = get_logger("page")
        self._modified = False
    
    @property
    def number(self) -> int:
        """Get page number (0-based)."""
        return self._page.number
    
    @property
    def rect(self) -> fitz.Rect:
        """Get page rectangle."""
        return self._page.rect
    
    @property
    def rotation(self) -> int:
        """Get page rotation in degrees."""
        return self._page.rotation
    
    @property
    def size(self) -> Tuple[float, float]:
        """Get page size (width, height)."""
        return (self._page.rect.width, self._page.rect.height)
    
    def get_text(self) -> str:
        """Extract text from page."""
        return self._page.get_text()
    
    def get_images(self) -> List[Dict[str, Any]]:
        """Get all images on the page."""
        return self._page.get_images()
    
    def get_annotations(self) -> List[Dict[str, Any]]:
        """Get all annotations on the page."""
        return self._page.annots()
    
    def rotate(self, angle: int) -> None:
        """Rotate page by specified degrees.
        
        Args:
            angle: Rotation angle (0, 90, 180, 270)
        """
        if angle not in [0, 90, 180, 270]:
            raise ValueError("Rotation angle must be 0, 90, 180, or 270")
        
        self._page.set_rotation(angle)
        self._modified = True
        self.logger.debug(f"Rotated page {self.number} by {angle} degrees")
    
    def add_text(self, text: str, position: Tuple[float, float], 
                 fontname: str = "helv", fontsize: float = 11, 
                 color: Tuple[float, float, float] = (0, 0, 0)) -> None:
        """Add text to page at specified position.
        
        Args:
            text: Text to add
            position: (x, y) coordinates
            fontname: Font name
            fontsize: Font size
            color: RGB color tuple
        """
        rect = fitz.Rect(position[0], position[1], position[0] + 100, position[1] + 20)
        self._page.insert_text(rect, text, fontname=fontname, fontsize=fontsize, color=color)
        self._modified = True
        self.logger.debug(f"Added text to page {self.number}: {text[:20]}...")
    
    def add_image(self, image_path: Union[str, Path], 
                  position: Tuple[float, float], 
                  width: Optional[float] = None, 
                  height: Optional[float] = None) -> None:
        """Add image to page at specified position.
        
        Args:
            image_path: Path to image file
            position: (x, y) coordinates
            width: Image width (optional)
            height: Image height (optional)
        """
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        # Insert image
        img_rect = fitz.Rect(position[0], position[1], 
                            position[0] + (width or 100), 
                            position[1] + (height or 100))
        
        self._page.insert_image(img_rect, filename=str(image_path))
        self._modified = True
        self.logger.debug(f"Added image to page {self.number}: {image_path.name}")
    
    def highlight_text(self, text: str, color: Tuple[float, float, float] = (1, 1, 0)) -> int:
        """Highlight all instances of text on page.
        
        Args:
            text: Text to highlight
            color: Highlight color (RGB tuple)
            
        Returns:
            Number of highlights added
        """
        areas = self._page.search_for(text)
        for area in areas:
            highlight = self._page.add_highlight_annot(area)
            highlight.set_colors({"stroke": color})
            highlight.update()
        
        self._modified = True
        self.logger.debug(f"Highlighted {len(areas)} instances of '{text}' on page {self.number}")
        return len(areas)
    
    def crop(self, rect: Tuple[float, float, float, float]) -> None:
        """Crop page to specified rectangle.
        
        Args:
            rect: (x0, y0, x1, y1) coordinates
        """
        crop_rect = fitz.Rect(rect)
        self._page.set_cropbox(crop_rect)
        self._modified = True
        self.logger.debug(f"Cropped page {self.number} to {rect}")
    
    def is_modified(self) -> bool:
        """Check if page has been modified."""
        return self._modified


class PDFDocument(BasePDFDocument):
    """PDF document implementation using PyMuPDF."""
    
    def __init__(self, file_path: Union[str, Path]):
        """Initialize PDF document.
        
        Args:
            file_path: Path to PDF file
        """
        super().__init__(file_path)
        
        try:
            self._doc = fitz.open(str(self.file_path))
            self._pages = [PDFPage(page) for page in self._doc]
            self._metadata = self._extract_metadata()
            self.logger.info(f"Opened PDF document: {self.file_path}")
            
        except Exception as e:
            raise PDFException(f"Failed to open PDF document: {e}")
    
    def _extract_metadata(self) -> Dict[str, Any]:
        """Extract metadata from PDF document."""
        metadata = self._doc.metadata.copy()
        
        # Add computed metadata
        metadata["page_count"] = len(self._pages)
        metadata["file_size"] = self.file_path.stat().st_size if self.file_path.exists() else 0
        metadata["created_time"] = datetime.fromtimestamp(self.file_path.stat().st_ctime).isoformat()
        metadata["modified_time"] = datetime.fromtimestamp(self.file_path.stat().st_mtime).isoformat()
        
        return metadata
    
    def get_page(self, page_number: int) -> PDFPage:
        """Get specific page.
        
        Args:
            page_number: Page number (0-based)
            
        Returns:
            PDF page object
        """
        if page_number < 0 or page_number >= len(self._pages):
            raise ValueError(f"Page number {page_number} out of range (0-{len(self._pages)-1})")
        
        return self._pages[page_number]
    
    def delete_page(self, page_number: int) -> None:
        """Delete a page.
        
        Args:
            page_number: Page number (0-based)
        """
        if page_number < 0 or page_number >= len(self._pages):
            raise ValueError(f"Page number {page_number} out of range")
        
        self._doc.delete_page(page_number)
        del self._pages[page_number]
        
        # Update page numbers
        for i, page in enumerate(self._pages):
            page._page = self._doc[i]
        
        self.mark_modified()
        self.logger.info(f"Deleted page {page_number}")
    
    def reorder_pages(self, new_order: List[int]) -> None:
        """Reorder pages.
        
        Args:
            new_order: New page order as list of page numbers (0-based)
        """
        if len(new_order) != len(self._pages):
            raise ValueError("New order must contain all page numbers")
        
        if set(new_order) != set(range(len(self._pages))):
            raise ValueError("New order must contain each page number exactly once")
        
        # Reorder in PyMuPDF
        self._doc.select(new_order)
        
        # Reorder internal pages list
        self._pages = [self._pages[i] for i in new_order]
        
        # Update page objects
        for i, page in enumerate(self._pages):
            page._page = self._doc[i]
        
        self.mark_modified()
        self.logger.info(f"Reordered pages: {new_order}")
    
    def insert_page(self, page_number: int, width: float = 612, height: float = 792) -> PDFPage:
        """Insert a blank page.
        
        Args:
            page_number: Position to insert page (0-based)
            width: Page width in points
            height: Page height in points
            
        Returns:
            New PDF page object
        """
        if page_number < 0 or page_number > len(self._pages):
            raise ValueError(f"Page number {page_number} out of range")
        
        self._doc.new_page(page_number, width=width, height=height)
        
        # Update pages list
        new_page = PDFPage(self._doc[page_number])
        self._pages.insert(page_number, new_page)
        
        # Update page numbers for subsequent pages
        for i in range(page_number + 1, len(self._pages)):
            self._pages[i]._page = self._doc[i]
        
        self.mark_modified()
        self.logger.info(f"Inserted blank page at position {page_number}")
        return new_page
    
    def save(self, file_path: Optional[Union[str, Path]] = None, 
             garbage_collect: bool = True, 
             deflate: bool = True) -> None:
        """Save the document.
        
        Args:
            file_path: Optional output path
            garbage_collect: Clean up unused objects
            deflate: Compress streams
        """
        output_path = Path(file_path) if file_path else self.file_path
        
        # Create output directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Apply compression settings from config
        if config_manager.get("compression"):
            deflate = True
        
        try:
            save_options = fitz.PDF_MDEFLATE if deflate else fitz.PDF_MNONE
            if garbage_collect:
                save_options |= fitz.PDF_MGARBAGE
            
            self._doc.save(str(output_path), garbage=garbage_collect, deflate=deflate)
            self.clear_modified_flag()
            
            # Update metadata
            self.file_path = output_path
            self._metadata = self._extract_metadata()
            
            self.logger.info(f"Saved document to: {output_path}")
            
        except Exception as e:
            raise PDFException(f"Failed to save document: {e}")
    
    def get_text(self) -> str:
        """Extract all text from document."""
        text = ""
        for page in self._pages:
            text += page.get_text() + "\n"
        return text
    
    def search(self, pattern: str) -> List[Dict[str, Any]]:
        """Search for text pattern in document.
        
        Args:
            pattern: Text pattern to search for
            
        Returns:
            List of search results with page numbers and positions
        """
        results = []
        for page_num, page in enumerate(self._pages):
            areas = page._page.search_for(pattern)
            for area in areas:
                results.append({
                    "page": page_num,
                    "rect": (area.x0, area.y0, area.x1, area.y1),
                    "text": pattern
                })
        
        return results
    
    def close(self) -> None:
        """Close the document."""
        if hasattr(self, '_doc'):
            self._doc.close()
            self.logger.info(f"Closed document: {self.file_path}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()