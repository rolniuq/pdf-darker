"""OCR operations for text extraction and recognition."""

import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import tempfile
import pytesseract
from PIL import Image
import fitz  # PyMuPDF

from ..core.base import BaseOperation, ProcessingError, ValidationError
from ..utils.logging import get_logger

logger = get_logger("operations.ocr")


class OCRExtractTextOperation(BaseOperation):
    """Extract text from PDF using OCR."""
    
    def __init__(self, pages: Optional[List[int]] = None, language: str = 'eng', 
                 dpi: int = 300, confidence_threshold: float = 60.0):
        super().__init__()
        self.pages = pages  # None means all pages
        self.language = language
        self.dpi = dpi
        self.confidence_threshold = confidence_threshold
        
    def validate(self, document) -> None:
        """Validate operation parameters."""
        if self.confidence_threshold < 0 or self.confidence_threshold > 100:
            raise ValidationError("Confidence threshold must be between 0 and 100")
        
        if self.dpi < 72 or self.dpi > 600:
            raise ValidationError("DPI must be between 72 and 600")
        
        # Check if Tesseract is available
        try:
            pytesseract.get_tesseract_version()
        except pytesseract.TesseractNotFoundError:
            raise ValidationError("Tesseract OCR engine not found. Please install Tesseract")
    
    def execute(self, document) -> Dict:
        """Execute OCR text extraction."""
        try:
            logger.info(f"Starting OCR text extraction on {len(document)} pages")
            
            results = []
            pages_to_process = self.pages or list(range(len(document)))
            
            for page_num in pages_to_process:
                if page_num >= len(document):
                    logger.warning(f"Page {page_num} does not exist, skipping")
                    continue
                
                page_result = self._extract_page_text(document, page_num)
                results.append(page_result)
            
            logger.info(f"OCR extraction completed for {len(results)} pages")
            
            return {
                'operation': 'ocr_extract_text',
                'results': results,
                'total_pages': len(results),
                'language': self.language,
                'dpi': self.dpi
            }
            
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            raise ProcessingError(f"OCR text extraction failed: {e}")
    
    def _extract_page_text(self, document, page_num: int) -> Dict:
        """Extract text from a specific page."""
        page = document[page_num]
        
        # Convert page to image
        matrix = fitz.Matrix(self.dpi / 72, self.dpi / 72)
        pix = page.get_pixmap(matrix=matrix)
        
        # Convert to PIL Image
        img_data = pix.tobytes("png")
        image = Image.open(io.BytesIO(img_data))
        
        # Perform OCR
        ocr_data = pytesseract.image_to_data(
            image, 
            lang=self.language,
            output_type=pytesseract.Output.DICT,
            config=f'--psm {self.dpi // 100 + 6}'
        )
        
        # Process OCR results
        text_blocks = []
        current_line = []
        last_y = None
        
        for i in range(len(ocr_data['text'])):
            text = ocr_data['text'][i].strip()
            if not text:
                continue
            
            confidence = ocr_data['conf'][i]
            if confidence < self.confidence_threshold:
                continue
            
            x, y, w, h = ocr_data['left'][i], ocr_data['top'][i], ocr_data['width'][i], ocr_data['height'][i]
            
            # Group text by lines
            if last_y is not None and abs(y - last_y) > 10:  # New line
                if current_line:
                    text_blocks.append({
                        'type': 'line',
                        'text': ' '.join([item['text'] for item in current_line]),
                        'confidence': sum(item['confidence'] for item in current_line) / len(current_line),
                        'bbox': self._merge_bboxes([item['bbox'] for item in current_line])
                    })
                    current_line = []
            
            current_line.append({
                'text': text,
                'confidence': confidence,
                'bbox': (x, y, x + w, y + h)
            })
            last_y = y
        
        # Add the last line
        if current_line:
            text_blocks.append({
                'type': 'line',
                'text': ' '.join([item['text'] for item in current_line]),
                'confidence': sum(item['confidence'] for item in current_line) / len(current_line),
                'bbox': self._merge_bboxes([item['bbox'] for item in current_line])
            })
        
        return {
            'page_number': page_num + 1,
            'text_blocks': text_blocks,
            'full_text': '\n'.join([block['text'] for block in text_blocks])
        }
    
    def _merge_bboxes(self, bboxes: List[Tuple]) -> Tuple:
        """Merge multiple bounding boxes into one."""
        if not bboxes:
            return (0, 0, 0, 0)
        
        x0 = min(bbox[0] for bbox in bboxes)
        y0 = min(bbox[1] for bbox in bboxes)
        x1 = max(bbox[2] for bbox in bboxes)
        y1 = max(bbox[3] for bbox in bboxes)
        
        return (x0, y0, x1, y1)


class OCREditTextOperation(BaseOperation):
    """Edit text in PDF using OCR and replacement."""
    
    def __init__(self, find_text: str, replace_text: str, 
                 pages: Optional[List[int]] = None, language: str = 'eng',
                 dpi: int = 300, confidence_threshold: float = 70.0):
        super().__init__()
        self.find_text = find_text
        self.replace_text = replace_text
        self.pages = pages
        self.language = language
        self.dpi = dpi
        self.confidence_threshold = confidence_threshold
    
    def validate(self, document) -> None:
        """Validate operation parameters."""
        if not self.find_text:
            raise ValidationError("Find text cannot be empty")
        
        if self.find_text == self.replace_text:
            raise ValidationError("Find and replace text cannot be the same")
    
    def execute(self, document) -> Dict:
        """Execute OCR-based text editing."""
        try:
            logger.info(f"Starting OCR text replacement: '{self.find_text}' -> '{self.replace_text}'")
            
            # First extract text using OCR
            extract_op = OCRExtractTextOperation(
                pages=self.pages, 
                language=self.language, 
                dpi=self.dpi,
                confidence_threshold=self.confidence_threshold
            )
            
            extract_result = extract_op.execute(document)
            
            # Find and replace text
            replacements = []
            for page_result in extract_result['results']:
                page_replacements = self._find_replace_in_page(page_result, self.find_text, self.replace_text)
                replacements.extend(page_replacements)
            
            # Apply replacements to document
            for replacement in replacements:
                self._apply_replacement(document, replacement)
            
            logger.info(f"Applied {len(replacements)} text replacements")
            
            return {
                'operation': 'ocr_edit_text',
                'find_text': self.find_text,
                'replace_text': self.replace_text,
                'replacements': replacements,
                'total_replacements': len(replacements)
            }
            
        except Exception as e:
            logger.error(f"OCR text editing failed: {e}")
            raise ProcessingError(f"OCR text editing failed: {e}")
    
    def _find_replace_in_page(self, page_result: Dict, find_text: str, replace_text: str) -> List[Dict]:
        """Find text occurrences in a page."""
        replacements = []
        page_num = page_result['page_number'] - 1
        
        for block in page_result['text_blocks']:
            if find_text.lower() in block['text'].lower():
                # Calculate replacement position
                bbox = block['bbox']
                
                replacements.append({
                    'page': page_num,
                    'bbox': bbox,
                    'original_text': block['text'],
                    'replacement_text': block['text'].replace(find_text, replace_text),
                    'confidence': block['confidence']
                })
        
        return replacements
    
    def _apply_replacement(self, document, replacement: Dict):
        """Apply text replacement to document."""
        page = document[replacement['page']]
        bbox = replacement['bbox']
        
        # Create a rectangle covering the text area
        rect = fitz.Rect(bbox)
        
        # Cover original text with white rectangle
        page.draw_rect(rect, color=fitz.utils.getColor('white'), fill=fitz.utils.getColor('white'))
        
        # Insert new text
        # Note: This is a simplified implementation
        # A more sophisticated implementation would handle font matching, text flow, etc.
        page.insert_text(
            (bbox[0], bbox[3] - 2),  # Position with small offset
            replacement['replacement_text'],
            fontsize=12,
            color=fitz.utils.getColor('black')
        )


class OCRSearchOperation(BaseOperation):
    """Search for text in PDF using OCR."""
    
    def __init__(self, search_text: str, pages: Optional[List[int]] = None,
                 language: str = 'eng', dpi: int = 300, confidence_threshold: float = 60.0):
        super().__init__()
        self.search_text = search_text
        self.pages = pages
        self.language = language
        self.dpi = dpi
        self.confidence_threshold = confidence_threshold
    
    def validate(self, document) -> None:
        """Validate operation parameters."""
        if not self.search_text:
            raise ValidationError("Search text cannot be empty")
    
    def execute(self, document) -> Dict:
        """Execute OCR text search."""
        try:
            logger.info(f"Searching for text: '{self.search_text}'")
            
            # Extract text using OCR
            extract_op = OCRExtractTextOperation(
                pages=self.pages,
                language=self.language,
                dpi=self.dpi,
                confidence_threshold=self.confidence_threshold
            )
            
            extract_result = extract_op.execute(document)
            
            # Search for matches
            matches = []
            for page_result in extract_result['results']:
                page_matches = self._search_in_page(page_result, self.search_text)
                matches.extend(page_matches)
            
            logger.info(f"Found {len(matches)} matches for '{self.search_text}'")
            
            return {
                'operation': 'ocr_search',
                'search_text': self.search_text,
                'matches': matches,
                'total_matches': len(matches)
            }
            
        except Exception as e:
            logger.error(f"OCR search failed: {e}")
            raise ProcessingError(f"OCR search failed: {e}")
    
    def _search_in_page(self, page_result: Dict, search_text: str) -> List[Dict]:
        """Search for text in a page."""
        matches = []
        page_num = page_result['page_number'] - 1
        search_lower = search_text.lower()
        
        for block in page_result['text_blocks']:
            if search_lower in block['text'].lower():
                matches.append({
                    'page': page_num,
                    'text': block['text'],
                    'bbox': block['bbox'],
                    'confidence': block['confidence']
                })
        
        return matches


# Import io for image processing
import io