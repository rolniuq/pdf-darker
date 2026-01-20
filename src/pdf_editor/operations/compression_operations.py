"""Compression and optimization operations."""

import os
from pathlib import Path
from typing import Dict, Optional, Tuple
import fitz  # PyMuPDF
from PIL import Image
import io

from ..core.base import BaseOperation, ProcessingError, ValidationError
from ..utils.logging import get_logger

logger = get_logger("operations.compression")


class CompressPDFOperation(BaseOperation):
    """Compress PDF to reduce file size."""
    
    def __init__(self, quality: int = 70, image_quality: int = 75,
                 compress_images: bool = True, compress_fonts: bool = True,
                 remove_metadata: bool = False, optimize: bool = True):
        super().__init__()
        self.quality = max(0, min(100, quality))
        self.image_quality = max(0, min(100, image_quality))
        self.compress_images = compress_images
        self.compress_fonts = compress_fonts
        self.remove_metadata = remove_metadata
        self.optimize = optimize
    
    def validate(self, document) -> None:
        """Validate compression parameters."""
        if self.quality < 0 or self.quality > 100:
            raise ValidationError("Quality must be between 0 and 100")
        
        if self.image_quality < 0 or self.image_quality > 100:
            raise ValidationError("Image quality must be between 0 and 100")
    
    def execute(self, document) -> Dict:
        """Execute PDF compression."""
        try:
            original_size = len(document.tobytes())
            logger.info(f"Starting PDF compression. Original size: {original_size:,} bytes")
            
            # Create new document with optimized settings
            optimized_doc = fitz.open()
            
            # Process each page
            for page_num in range(len(document)):
                self._compress_page(document, optimized_doc, page_num)
            
            # Optimize the document
            if self.optimize:
                optimized_doc.save(
                    io.BytesIO(),
                    garbage=4,  # Clean up all objects
                    deflate=True,
                    clean=True
                )
            
            # Calculate compression statistics
            optimized_bytes = optimized_doc.tobytes()
            optimized_size = len(optimized_bytes)
            compression_ratio = ((original_size - optimized_size) / original_size * 100) if original_size > 0 else 0
            
            logger.info(f"Compression completed. New size: {optimized_size:,} bytes ({compression_ratio:.1f}% reduction)")
            
            # Replace original document with optimized one
            document._delete_pages(range(len(document)))
            document.insert_pdf(optimized_doc)
            
            return {
                'operation': 'compress_pdf',
                'original_size': original_size,
                'compressed_size': optimized_size,
                'compression_ratio': compression_ratio,
                'settings': {
                    'quality': self.quality,
                    'image_quality': self.image_quality,
                    'compress_images': self.compress_images,
                    'compress_fonts': self.compress_fonts,
                    'remove_metadata': self.remove_metadata,
                    'optimize': self.optimize
                }
            }
            
        except Exception as e:
            logger.error(f"PDF compression failed: {e}")
            raise ProcessingError(f"PDF compression failed: {e}")
    
    def _compress_page(self, source_doc, target_doc, page_num: int):
        """Compress a single page."""
        source_page = source_doc[page_num]
        
        # Get page size
        rect = source_page.rect
        target_page = target_doc.new_page(width=rect.width, height=rect.height)
        
        # Extract and compress images
        if self.compress_images:
            self._compress_page_images(source_page, target_page)
        else:
            # Copy page as-is
            target_page.show_pdf_page(rect, source_doc, page_num)
        
        # Copy text and annotations
        self._copy_page_content(source_page, target_page)
    
    def _compress_page_images(self, source_page, target_page):
        """Compress images in a page."""
        # Get page as image
        pix = source_page.get_pixmap()
        
        # Compress image
        img_data = pix.tobytes("jpeg", quality=self.image_quality)
        
        # Create image from compressed data
        img = Image.open(io.BytesIO(img_data))
        
        # Convert back to pixmap and insert
        img_pixmap = fitz.Pixmap(io.BytesIO(img_data))
        target_page.insert_image(target_page.rect, pixmap=img_pixmap)
    
    def _copy_page_content(self, source_page, target_page):
        """Copy text and annotations from source to target page."""
        # Copy text (simplified - in practice, you'd want more sophisticated text handling)
        text = source_page.get_text()
        if text.strip():
            # This is a simplified approach
            # In reality, you'd need to preserve text positioning and formatting
            target_page.insert_text((50, 50), text, fontsize=12)
        
        # Copy annotations
        for annot in source_page.annotations():
            target_page.add_annot(annot)


class OptimizeImagesOperation(BaseOperation):
    """Optimize images in PDF for better compression."""
    
    def __init__(self, max_resolution: int = 150, jpeg_quality: int = 80,
                 remove_unused_images: bool = True, convert_to_grayscale: bool = False):
        super().__init__()
        self.max_resolution = max_resolution
        self.jpeg_quality = jpeg_quality
        self.remove_unused_images = remove_unused_images
        self.convert_to_grayscale = convert_to_grayscale
    
    def validate(self, document) -> None:
        """Validate optimization parameters."""
        if self.max_resolution < 72 or self.max_resolution > 300:
            raise ValidationError("Max resolution must be between 72 and 300 DPI")
        
        if self.jpeg_quality < 0 or self.jpeg_quality > 100:
            raise ValidationError("JPEG quality must be between 0 and 100")
    
    def execute(self, document) -> Dict:
        """Execute image optimization."""
        try:
            logger.info(f"Starting image optimization with max resolution: {self.max_resolution} DPI")
            
            original_images = self._extract_images(document)
            optimized_images = []
            total_original_size = 0
            total_optimized_size = 0
            
            for img_info in original_images:
                # Optimize image
                optimized_img = self._optimize_image(img_info)
                optimized_images.append(optimized_img)
                
                total_original_size += len(img_info['data'])
                total_optimized_size += len(optimized_img['data'])
            
            # Replace images in document
            self._replace_images(document, optimized_images)
            
            # Calculate optimization statistics
            size_reduction = ((total_original_size - total_optimized_size) / total_original_size * 100) if total_original_size > 0 else 0
            
            logger.info(f"Image optimization completed. Size reduction: {size_reduction:.1f}%")
            
            return {
                'operation': 'optimize_images',
                'original_images': len(original_images),
                'optimized_images': len(optimized_images),
                'original_size': total_original_size,
                'optimized_size': total_optimized_size,
                'size_reduction': size_reduction,
                'settings': {
                    'max_resolution': self.max_resolution,
                    'jpeg_quality': self.jpeg_quality,
                    'remove_unused_images': self.remove_unused_images,
                    'convert_to_grayscale': self.convert_to_grayscale
                }
            }
            
        except Exception as e:
            logger.error(f"Image optimization failed: {e}")
            raise ProcessingError(f"Image optimization failed: {e}")
    
    def _extract_images(self, document) -> list:
        """Extract all images from PDF."""
        images = []
        
        for page_num in range(len(document)):
            page = document[page_num]
            image_list = page.get_images()
            
            for img_index, img in enumerate(image_list):
                # Get image data
                xref = img[0]
                pix = fitz.Pixmap(document, xref)
                
                if pix.n - pix.alpha < 4:  # Ensure it's not a mask or CMYK
                    img_data = pix.tobytes("png")
                    images.append({
                        'page': page_num,
                        'index': img_index,
                        'data': img_data,
                        'width': pix.width,
                        'height': pix.height,
                        'colorspace': pix.n
                    })
                
                pix = None  # Free memory
        
        return images
    
    def _optimize_image(self, img_info: Dict) -> Dict:
        """Optimize a single image."""
        try:
            # Load image
            img = Image.open(io.BytesIO(img_info['data']))
            
            # Calculate current resolution
            # Assuming 72 DPI as base resolution (this is approximate)
            current_resolution = 72
            
            # Resize if necessary
            if current_resolution > self.max_resolution:
                scale_factor = self.max_resolution / current_resolution
                new_width = int(img_info['width'] * scale_factor)
                new_height = int(img_info['height'] * scale_factor)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert to grayscale if requested
            if self.convert_to_grayscale and img.mode != 'L':
                img = img.convert('L')
            
            # Convert to JPEG with quality setting
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Save optimized image
            optimized_data = io.BytesIO()
            img.save(optimized_data, format='JPEG', quality=self.jpeg_quality, optimize=True)
            
            return {
                'page': img_info['page'],
                'index': img_info['index'],
                'data': optimized_data.getvalue(),
                'width': img.width,
                'height': img.height
            }
            
        except Exception as e:
            logger.warning(f"Failed to optimize image: {e}")
            return img_info  # Return original if optimization fails
    
    def _replace_images(self, document, optimized_images: list):
        """Replace images in document with optimized versions."""
        # This is a simplified implementation
        # In practice, you'd need to replace images by their cross-references
        pass


class CleanupPDFOperation(BaseOperation):
    """Clean up PDF by removing unused elements."""
    
    def __init__(self, remove_unused_fonts: bool = True, 
                 remove_unused_images: bool = True,
                 remove_duplicates: bool = True, 
                 compress_content_streams: bool = True):
        super().__init__()
        self.remove_unused_fonts = remove_unused_fonts
        self.remove_unused_images = remove_unused_images
        self.remove_duplicates = remove_duplicates
        self.compress_content_streams = compress_content_streams
    
    def validate(self, document) -> None:
        """Validate cleanup parameters."""
        pass  # All parameters are boolean and valid by default
    
    def execute(self, document) -> Dict:
        """Execute PDF cleanup."""
        try:
            original_size = len(document.tobytes())
            logger.info("Starting PDF cleanup")
            
            # Save with cleanup options
            cleaned_bytes = io.BytesIO()
            document.save(
                cleaned_bytes,
                garbage=4 if self.remove_unused_fonts else 1,  # 4 = remove all unused objects
                deflate=self.compress_content_streams,
                clean=self.remove_duplicates,
                ascii=False
            )
            
            cleaned_size = len(cleaned_bytes.getvalue())
            size_reduction = ((original_size - cleaned_size) / original_size * 100) if original_size > 0 else 0
            
            logger.info(f"PDF cleanup completed. Size reduction: {size_reduction:.1f}%")
            
            # Update document with cleaned version
            cleaned_doc = fitz.open(stream=cleaned_bytes.getvalue())
            document._delete_pages(range(len(document)))
            document.insert_pdf(cleaned_doc)
            
            return {
                'operation': 'cleanup_pdf',
                'original_size': original_size,
                'cleaned_size': cleaned_size,
                'size_reduction': size_reduction,
                'settings': {
                    'remove_unused_fonts': self.remove_unused_fonts,
                    'remove_unused_images': self.remove_unused_images,
                    'remove_duplicates': self.remove_duplicates,
                    'compress_content_streams': self.compress_content_streams
                }
            }
            
        except Exception as e:
            logger.error(f"PDF cleanup failed: {e}")
            raise ProcessingError(f"PDF cleanup failed: {e}")


class AnalyzePDFOperation(BaseOperation):
    """Analyze PDF structure and provide optimization suggestions."""
    
    def __init__(self):
        super().__init__()
    
    def validate(self, document) -> None:
        """Validate analysis parameters."""
        pass
    
    def execute(self, document) -> Dict:
        """Analyze PDF and provide recommendations."""
        try:
            logger.info("Starting PDF analysis")
            
            analysis = {
                'total_pages': len(document),
                'file_size': len(document.tobytes()),
                'images': self._analyze_images(document),
                'fonts': self._analyze_fonts(document),
                'content': self._analyze_content(document),
                'metadata': self._analyze_metadata(document),
                'recommendations': []
            }
            
            # Generate recommendations
            analysis['recommendations'] = self._generate_recommendations(analysis)
            
            logger.info("PDF analysis completed")
            
            return {
                'operation': 'analyze_pdf',
                'analysis': analysis
            }
            
        except Exception as e:
            logger.error(f"PDF analysis failed: {e}")
            raise ProcessingError(f"PDF analysis failed: {e}")
    
    def _analyze_images(self, document) -> Dict:
        """Analyze images in PDF."""
        image_stats = {
            'total_images': 0,
            'total_size': 0,
            'average_resolution': 0,
            'has_large_images': False
        }
        
        resolutions = []
        
        for page_num in range(len(document)):
            page = document[page_num]
            image_list = page.get_images()
            
            for img in image_list:
                xref = img[0]
                pix = fitz.Pixmap(document, xref)
                
                if pix.n - pix.alpha < 4:  # Not a mask or CMYK
                    image_stats['total_images'] += 1
                    image_stats['total_size'] += len(pix.tobytes())
                    
                    # Estimate resolution (this is approximate)
                    if pix.width > 1000 or pix.height > 1000:
                        image_stats['has_large_images'] = True
                    
                    resolutions.append(max(pix.width, pix.height))
                
                pix = None
        
        if resolutions:
            image_stats['average_resolution'] = sum(resolutions) / len(resolutions)
        
        return image_stats
    
    def _analyze_fonts(self, document) -> Dict:
        """Analyze fonts in PDF."""
        font_stats = {
            'total_fonts': 0,
            'embedded_fonts': 0,
            'has_non_embedded_fonts': False
        }
        
        for page_num in range(len(document)):
            page = document[page_num]
            text_dict = page.get_text("dict")
            
            for block in text_dict.get("blocks", []):
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            if "font" in span:
                                font_stats['total_fonts'] += 1
                                # Check if font is embedded (simplified check)
                                if "embedded" in str(span.get("font", "")).lower():
                                    font_stats['embedded_fonts'] += 1
                                else:
                                    font_stats['has_non_embedded_fonts'] = True
        
        return font_stats
    
    def _analyze_content(self, document) -> Dict:
        """Analyze content in PDF."""
        content_stats = {
            'total_words': 0,
            'total_characters': 0,
            'has_annotations': False,
            'has_forms': False
        }
        
        for page_num in range(len(document)):
            page = document[page_num]
            
            # Count text
            text = page.get_text()
            content_stats['total_words'] += len(text.split())
            content_stats['total_characters'] += len(text)
            
            # Check for annotations
            if page.first_annot:
                content_stats['has_annotations'] = True
            
            # Check for forms
            if page.widgets():
                content_stats['has_forms'] = True
        
        return content_stats
    
    def _analyze_metadata(self, document) -> Dict:
        """Analyze PDF metadata."""
        metadata = document.metadata
        return {
            'has_title': bool(metadata.get('title')),
            'has_author': bool(metadata.get('author')),
            'has_subject': bool(metadata.get('subject')),
            'has_keywords': bool(metadata.get('keywords')),
            'creator': metadata.get('creator', ''),
            'producer': metadata.get('producer', ''),
            'creation_date': metadata.get('creationDate', ''),
            'modification_date': metadata.get('modDate', '')
        }
    
    def _generate_recommendations(self, analysis: Dict) -> list:
        """Generate optimization recommendations."""
        recommendations = []
        
        # Image recommendations
        if analysis['images']['has_large_images']:
            recommendations.append({
                'type': 'images',
                'priority': 'high',
                'description': 'Large images detected. Consider optimizing image quality.',
                'suggested_operation': 'optimize_images'
            })
        
        if analysis['images']['total_images'] > 10:
            recommendations.append({
                'type': 'images',
                'priority': 'medium',
                'description': 'Many images detected. Consider compressing images.',
                'suggested_operation': 'compress_pdf'
            })
        
        # Font recommendations
        if analysis['fonts']['has_non_embedded_fonts']:
            recommendations.append({
                'type': 'fonts',
                'priority': 'medium',
                'description': 'Non-embedded fonts detected. Consider embedding fonts.',
                'suggested_operation': 'embed_fonts'
            })
        
        # Content recommendations
        if analysis['content']['total_words'] > 10000:
            recommendations.append({
                'type': 'content',
                'priority': 'low',
                'description': 'Large document detected. Consider compression.',
                'suggested_operation': 'compress_pdf'
            })
        
        # File size recommendations
        file_size_mb = analysis['file_size'] / (1024 * 1024)
        if file_size_mb > 10:
            recommendations.append({
                'type': 'size',
                'priority': 'high',
                'description': f'Large file size ({file_size_mb:.1f} MB). Consider optimization.',
                'suggested_operation': 'compress_pdf'
            })
        
        return recommendations