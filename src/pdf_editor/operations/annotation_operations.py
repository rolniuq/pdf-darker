"""Annotation operations for PDF editing."""

import fitz  # PyMuPDF
from datetime import datetime

from ..core.base import BaseOperation, OperationType, OperationResult, PDFDocument


class AnnotationOperation(BaseOperation):
    """Base class for annotation operations."""
    
    def __init__(self, operation_type: OperationType):
        super().__init__(operation_type)


class AddAnnotationOperation(AnnotationOperation):
    """Operation to add annotations to PDF."""
    
    def __init__(self, page_number: int, rect: tuple, annotation_type: str, 
                 content: str = None, author: str = None, color: tuple = None):
        super().__init__(OperationType.ADD_ANNOTATION)
        
        self.set_parameter("page_number", page_number)
        self.set_parameter("rect", rect)
        self.set_parameter("annotation_type", annotation_type)
        self.set_parameter("content", content)
        self.set_parameter("author", author)
        self.set_parameter("color", color or (1, 0, 0))  # Default red
    
    def validate(self, document: PDFDocument) -> bool:
        """Validate annotation creation parameters."""
        if not super().validate(document):
            return False
        
        page_number = self.get_parameter("page_number")
        rect = self.get_parameter("rect")
        annotation_type = self.get_parameter("annotation_type")
        
        # Validate page number
        if not isinstance(page_number, int) or page_number < 0 or page_number >= document.page_count:
            self.logger.error(f"Invalid page number: {page_number}")
            return False
        
        # Validate rectangle
        if (not isinstance(rect, tuple) or len(rect) != 4 or 
            not all(isinstance(x, (int, float)) for x in rect)):
            self.logger.error("Rect must be a tuple of 4 numbers (x0, y0, x1, y1)")
            return False
        
        # Validate annotation type
        valid_types = ["text", "highlight", "underline", "strikeout", "squiggly", 
                     "note", "popup", "free_text", "line", "arrow", "rectangle", 
                     "circle", "polygon", "polyline"]
        if annotation_type not in valid_types:
            self.logger.error(f"Invalid annotation type: {annotation_type}. Must be one of {valid_types}")
            return False
        
        return True
    
    def execute(self, document: PDFDocument) -> OperationResult:
        """Execute annotation creation."""
        try:
            page_number = self.get_parameter("page_number")
            rect = self.get_parameter("rect")
            annotation_type = self.get_parameter("annotation_type")
            content = self.get_parameter("content")
            author = self.get_parameter("author")
            color = self.get_parameter("color")
            
            page = document.get_page(page_number)
            
            # Create annotation based on type
            if annotation_type == "text":
                annot = self._create_text_annotation(page, rect, content, author, color)
            elif annotation_type == "highlight":
                annot = self._create_highlight_annotation(page, rect, content, color)
            elif annotation_type == "underline":
                annot = self._create_underline_annotation(page, rect, color)
            elif annotation_type == "strikeout":
                annot = self._create_strikeout_annotation(page, rect, color)
            elif annotation_type == "squiggly":
                annot = self._create_squiggly_annotation(page, rect, color)
            elif annotation_type == "note":
                annot = self._create_note_annotation(page, rect, content, author, color)
            elif annotation_type == "free_text":
                annot = self._create_free_text_annotation(page, rect, content, color)
            elif annotation_type == "line":
                annot = self._create_line_annotation(page, rect, color)
            elif annotation_type == "arrow":
                annot = self._create_arrow_annotation(page, rect, color)
            elif annotation_type == "rectangle":
                annot = self._create_rectangle_annotation(page, rect, color)
            elif annotation_type == "circle":
                annot = self._create_circle_annotation(page, rect, color)
            else:
                self.logger.error(f"Unsupported annotation type: {annotation_type}")
                return OperationResult.FAILED
            
            document.mark_modified()
            self.logger.info(f"Added {annotation_type} annotation on page {page_number}")
            
            return OperationResult.SUCCESS
            
        except Exception as e:
            self.logger.error(f"Failed to create annotation: {e}")
            return OperationResult.FAILED
    
    def _create_text_annotation(self, page, rect, content, author, color):
        """Create a text annotation."""
        annot = page.add_text_annot(rect, content or "")
        if author:
            annot.set_author(author)
        if color:
            annot.set_colors(stroke=color)
        return annot
    
    def _create_highlight_annotation(self, page, rect, content, color):
        """Create a highlight annotation."""
        annot = page.add_highlight_annot(rect, content or "")
        if color:
            annot.set_colors(stroke=color)
        return annot
    
    def _create_underline_annotation(self, page, rect, color):
        """Create an underline annotation."""
        annot = page.add_underline_annot(rect)
        if color:
            annot.set_colors(stroke=color)
        return annot
    
    def _create_strikeout_annotation(self, page, rect, color):
        """Create a strikeout annotation."""
        annot = page.add_strikeout_annot(rect)
        if color:
            annot.set_colors(stroke=color)
        return annot
    
    def _create_squiggly_annotation(self, page, rect, color):
        """Create a squiggly underline annotation."""
        annot = page.add_squiggly_annot(rect)
        if color:
            annot.set_colors(stroke=color)
        return annot
    
    def _create_note_annotation(self, page, rect, content, author, color):
        """Create a note annotation."""
        annot = page.add_text_annot(rect, content or "")
        annot.set_icon("Note")
        if author:
            annot.set_author(author)
        if color:
            annot.set_colors(stroke=color)
        return annot
    
    def _create_free_text_annotation(self, page, rect, content, color):
        """Create a free text annotation."""
        annot = page.add_freetext_annot(rect, content or "")
        if color:
            annot.set_colors(stroke=color)
        return annot
    
    def _create_line_annotation(self, page, rect, color):
        """Create a line annotation."""
        # rect contains (x1, y1, x2, y2) for line
        if len(rect) == 4:
            points = [(rect[0], rect[1]), (rect[2], rect[3])]
            annot = page.add_line_annot(points)
            if color:
                annot.set_colors(stroke=color)
            return annot
        return None
    
    def _create_arrow_annotation(self, page, rect, color):
        """Create an arrow annotation."""
        if len(rect) == 4:
            points = [(rect[0], rect[1]), (rect[2], rect[3])]
            annot = page.add_line_annot(points, line_ending={"start": None, "end": "OpenArrow"})
            if color:
                annot.set_colors(stroke=color)
            return annot
        return None
    
    def _create_rectangle_annotation(self, page, rect, color):
        """Create a rectangle annotation."""
        annot = page.add_rect_annot(rect)
        if color:
            annot.set_colors(stroke=color, fill=(*color, 0.1))  # Light fill
        return annot
    
    def _create_circle_annotation(self, page, rect, color):
        """Create a circle annotation."""
        # Calculate center and radius from rect
        center_x = (rect[0] + rect[2]) / 2
        center_y = (rect[1] + rect[3]) / 2
        radius = min(rect[2] - rect[0], rect[3] - rect[1]) / 2
        
        quad = fitz.Quad(rect)
        annot = page.add_quad_annot(quad)
        if color:
            annot.set_colors(stroke=color, fill=(*color, 0.1))
        return annot


class AddCommentOperation(AnnotationOperation):
    """Operation to add comments to PDF."""
    
    def __init__(self, page_number: int, position: tuple, comment: str, 
                 author: str = None, reply_to: str = None):
        super().__init__(OperationType.ADD_COMMENT)
        
        self.set_parameter("page_number", page_number)
        self.set_parameter("position", position)
        self.set_parameter("comment", comment)
        self.set_parameter("author", author)
        self.set_parameter("reply_to", reply_to)
    
    def validate(self, document: PDFDocument) -> bool:
        """Validate comment creation parameters."""
        if not super().validate(document):
            return False
        
        page_number = self.get_parameter("page_number")
        position = self.get_parameter("position")
        comment = self.get_parameter("comment")
        
        # Validate page number
        if not isinstance(page_number, int) or page_number < 0 or page_number >= document.page_count:
            self.logger.error(f"Invalid page number: {page_number}")
            return False
        
        # Validate position
        if (not isinstance(position, tuple) or len(position) != 2 or 
            not all(isinstance(x, (int, float)) for x in position)):
            self.logger.error("Position must be a tuple of 2 numbers (x, y)")
            return False
        
        # Validate comment
        if not comment or not isinstance(comment, str):
            self.logger.error("Comment must be a non-empty string")
            return False
        
        return True
    
    def execute(self, document: PDFDocument) -> OperationResult:
        """Execute comment creation."""
        try:
            page_number = self.get_parameter("page_number")
            position = self.get_parameter("position")
            comment = self.get_parameter("comment")
            author = self.get_parameter("author")
            reply_to = self.get_parameter("reply_to")
            
            page = document.get_page(page_number)
            
            # Create a small rectangle around the position for the comment
            rect = (position[0] - 5, position[1] - 5, position[0] + 5, position[1] + 5)
            
            # Create text annotation with comment icon
            annot = page.add_text_annot(rect, comment)
            annot.set_icon("Comment")
            
            if author:
                annot.set_author(author)
            
            # Set creation time
            annot.set_creation_date(datetime.now())
            
            # If replying to another comment, add that information
            if reply_to:
                # In a real implementation, you'd link this to the parent comment
                annot.set_info("reply_to", reply_to)
            
            document.mark_modified()
            self.logger.info(f"Added comment on page {page_number} at position {position}")
            
            return OperationResult.SUCCESS
            
        except Exception as e:
            self.logger.error(f"Failed to add comment: {e}")
            return OperationResult.FAILED


class AddDrawingOperation(AnnotationOperation):
    """Operation to add drawing annotations (shapes, arrows)."""
    
    def __init__(self, page_number: int, drawing_type: str, points: list,
                 color: tuple = None, thickness: float = 1.0, fill: bool = False):
        super().__init__(OperationType.ADD_DRAWING)
        
        self.set_parameter("page_number", page_number)
        self.set_parameter("drawing_type", drawing_type)
        self.set_parameter("points", points)
        self.set_parameter("color", color or (0, 0, 1))  # Default blue
        self.set_parameter("thickness", thickness)
        self.set_parameter("fill", fill)
    
    def validate(self, document: PDFDocument) -> bool:
        """Validate drawing creation parameters."""
        if not super().validate(document):
            return False
        
        page_number = self.get_parameter("page_number")
        drawing_type = self.get_parameter("drawing_type")
        points = self.get_parameter("points")
        
        # Validate page number
        if not isinstance(page_number, int) or page_number < 0 or page_number >= document.page_count:
            self.logger.error(f"Invalid page number: {page_number}")
            return False
        
        # Validate drawing type
        valid_types = ["line", "polygon", "polyline", "rectangle", "ellipse"]
        if drawing_type not in valid_types:
            self.logger.error(f"Invalid drawing type: {drawing_type}. Must be one of {valid_types}")
            return False
        
        # Validate points
        if not isinstance(points, list) or len(points) < 2:
            self.logger.error("Points must be a list with at least 2 points")
            return False
        
        for point in points:
            if (not isinstance(point, (tuple, list)) or len(point) != 2 or 
                not all(isinstance(x, (int, float)) for x in point)):
                self.logger.error("Each point must be a tuple/list of 2 numbers (x, y)")
                return False
        
        return True
    
    def execute(self, document: PDFDocument) -> OperationResult:
        """Execute drawing creation."""
        try:
            page_number = self.get_parameter("page_number")
            drawing_type = self.get_parameter("drawing_type")
            points = self.get_parameter("points")
            color = self.get_parameter("color")
            thickness = self.get_parameter("thickness")
            fill = self.get_parameter("fill")
            
            page = document.get_page(page_number)
            
            # Create drawing based on type
            if drawing_type == "line":
                annot = self._create_line_drawing(page, points, color, thickness)
            elif drawing_type == "polygon":
                annot = self._create_polygon_drawing(page, points, color, thickness, fill)
            elif drawing_type == "polyline":
                annot = self._create_polyline_drawing(page, points, color, thickness)
            elif drawing_type == "rectangle":
                annot = self._create_rectangle_drawing(page, points, color, thickness, fill)
            elif drawing_type == "ellipse":
                annot = self._create_ellipse_drawing(page, points, color, thickness, fill)
            else:
                self.logger.error(f"Unsupported drawing type: {drawing_type}")
                return OperationResult.FAILED
            
            document.mark_modified()
            self.logger.info(f"Added {drawing_type} drawing on page {page_number}")
            
            return OperationResult.SUCCESS
            
        except Exception as e:
            self.logger.error(f"Failed to create drawing: {e}")
            return OperationResult.FAILED
    
    def _create_line_drawing(self, page, points, color, thickness):
        """Create a line drawing."""
        if len(points) >= 2:
            line_points = [(points[0][0], points[0][1]), (points[1][0], points[1][1])]
            annot = page.add_line_annot(line_points)
            if color:
                annot.set_colors(stroke=color)
            annot.set_border(width=thickness)
            return annot
        return None
    
    def _create_polyline_drawing(self, page, points, color, thickness):
        """Create a polyline drawing."""
        if len(points) >= 2:
            line_points = [(p[0], p[1]) for p in points]
            annot = page.add_polyline_annot(line_points)
            if color:
                annot.set_colors(stroke=color)
            annot.set_border(width=thickness)
            return annot
        return None
    
    def _create_rectangle_drawing(self, page, points, color, thickness, fill):
        """Create a rectangle drawing."""
        if len(points) >= 2:
            # Use first two points as opposite corners
            x0, y0 = points[0]
            x1, y1 = points[1]
            rect = (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))
            
            annot = page.add_rect_annot(rect)
            if color:
                if fill:
                    annot.set_colors(stroke=color, fill=(*color, 0.2))
                else:
                    annot.set_colors(stroke=color)
            annot.set_border(width=thickness)
            return annot
        return None
    
    def _create_ellipse_drawing(self, page, points, color, thickness, fill):
        """Create an ellipse drawing."""
        if len(points) >= 2:
            # Use first two points as bounding box
            x0, y0 = points[0]
            x1, y1 = points[1]
            rect = (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))
            
            quad = fitz.Quad(rect)
            annot = page.add_quad_annot(quad)
            if color:
                if fill:
                    annot.set_colors(stroke=color, fill=(*color, 0.2))
                else:
                    annot.set_colors(stroke=color)
            annot.set_border(width=thickness)
            return annot
        return None
    
    def _create_polygon_drawing(self, page, points, color, thickness, fill):
        """Create a polygon drawing."""
        if len(points) >= 3:
            polygon_points = [(p[0], p[1]) for p in points]
            annot = page.add_polyline_annot(polygon_points + [polygon_points[0]])  # Close the polygon
            if color:
                if fill:
                    annot.set_colors(stroke=color, fill=(*color, 0.2))
                else:
                    annot.set_colors(stroke=color)
            annot.set_border(width=thickness)
            return annot
        return None


class AddFreehandOperation(AnnotationOperation):
    """Operation to add freehand drawing annotations."""
    
    def __init__(self, page_number: int, strokes: list, color: tuple = None, 
                 thickness: float = 1.0):
        super().__init__(OperationType.ADD_FREEHAND)
        
        self.set_parameter("page_number", page_number)
        self.set_parameter("strokes", strokes)
        self.set_parameter("color", color or (0, 0, 0))  # Default black
        self.set_parameter("thickness", thickness)
    
    def validate(self, document: PDFDocument) -> bool:
        """Validate freehand drawing parameters."""
        if not super().validate(document):
            return False
        
        page_number = self.get_parameter("page_number")
        strokes = self.get_parameter("strokes")
        
        # Validate page number
        if not isinstance(page_number, int) or page_number < 0 or page_number >= document.page_count:
            self.logger.error(f"Invalid page number: {page_number}")
            return False
        
        # Validate strokes
        if not isinstance(strokes, list) or not strokes:
            self.logger.error("Strokes must be a non-empty list")
            return False
        
        for stroke in strokes:
            if (not isinstance(stroke, list) or len(stroke) < 2 or
                not all(isinstance(p, (tuple, list)) and len(p) == 2 and 
                       all(isinstance(x, (int, float)) for x in p) for p in stroke)):
                self.logger.error("Each stroke must be a list of (x, y) points")
                return False
        
        return True
    
    def execute(self, document: PDFDocument) -> OperationResult:
        """Execute freehand drawing creation."""
        try:
            page_number = self.get_parameter("page_number")
            strokes = self.get_parameter("strokes")
            color = self.get_parameter("color")
            thickness = self.get_parameter("thickness")
            
            page = document.get_page(page_number)
            
            # Create polyline annotations for each stroke
            for stroke in strokes:
                if len(stroke) >= 2:
                    points = [(p[0], p[1]) for p in stroke]
                    annot = page.add_polyline_annot(points)
                    
                    if color:
                        annot.set_colors(stroke=color)
                    annot.set_border(width=thickness)
            
            document.mark_modified()
            total_strokes = len(strokes)
            self.logger.info(f"Added freehand drawing with {total_strokes} strokes on page {page_number}")
            
            return OperationResult.SUCCESS
            
        except Exception as e:
            self.logger.error(f"Failed to create freehand drawing: {e}")
            return OperationResult.FAILED