"""Error handling and validation utilities."""

from typing import Any, Dict, List, Optional, Union, Callable
from pathlib import Path
import functools

from .base import PDFException, ValidationError, ProcessingError
from ..utils.logging import get_logger


class Validator:
    """Utility class for common validation operations."""
    
    @staticmethod
    def validate_file_path(file_path: Union[str, Path], 
                          must_exist: bool = True, 
                          extensions: Optional[List[str]] = None) -> Path:
        """Validate file path.
        
        Args:
            file_path: Path to validate
            must_exist: Whether file must exist
            extensions: Allowed file extensions (including dot)
            
        Returns:
            Validated Path object
            
        Raises:
            ValidationError: If validation fails
        """
        path = Path(file_path)
        
        # Check if path is valid
        if not path.parent.exists():
            raise ValidationError(f"Parent directory does not exist: {path.parent}")
        
        # Check if file exists (if required)
        if must_exist and not path.exists():
            raise ValidationError(f"File does not exist: {path}")
        
        # Check file extension
        if extensions and path.exists():
            if path.suffix.lower() not in [ext.lower() for ext in extensions]:
                raise ValidationError(f"File extension not allowed. Expected: {extensions}, Got: {path.suffix}")
        
        return path
    
    @staticmethod
    def validate_page_number(page_number: int, max_pages: int) -> int:
        """Validate page number.
        
        Args:
            page_number: Page number to validate
            max_pages: Maximum number of pages
            
        Returns:
            Validated page number
            
        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(page_number, int):
            raise ValidationError(f"Page number must be an integer, got: {type(page_number)}")
        
        if page_number < 0:
            raise ValidationError(f"Page number cannot be negative: {page_number}")
        
        if page_number >= max_pages:
            raise ValidationError(f"Page number {page_number} out of range (0-{max_pages-1})")
        
        return page_number
    
    @staticmethod
    def validate_rotation_angle(angle: int) -> int:
        """Validate rotation angle.
        
        Args:
            angle: Angle in degrees
            
        Returns:
            Validated angle
            
        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(angle, int):
            raise ValidationError(f"Angle must be an integer, got: {type(angle)}")
        
        if angle not in [0, 90, 180, 270]:
            raise ValidationError(f"Invalid rotation angle: {angle}. Must be 0, 90, 180, or 270")
        
        return angle
    
    @staticmethod
    def validate_dpi(dpi: Any) -> int:
        """Validate DPI value.
        
        Args:
            dpi: DPI value to validate
            
        Returns:
            Validated DPI
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            dpi_int = int(dpi)
        except (ValueError, TypeError):
            raise ValidationError(f"DPI must be a number, got: {type(dpi)}")
        
        if dpi_int < 72 or dpi_int > 600:
            raise ValidationError(f"DPI must be between 72 and 600, got: {dpi_int}")
        
        return dpi_int
    
    @staticmethod
    def validate_quality(quality: Any) -> int:
        """Validate quality value.
        
        Args:
            quality: Quality value to validate (1-100)
            
        Returns:
            Validated quality
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            quality_int = int(quality)
        except (ValueError, TypeError):
            raise ValidationError(f"Quality must be a number, got: {type(quality)}")
        
        if quality_int < 1 or quality_int > 100:
            raise ValidationError(f"Quality must be between 1 and 100, got: {quality_int}")
        
        return quality_int
    
    @staticmethod
    def validate_coordinates(position: Any, name: str = "position") -> tuple:
        """Validate coordinate tuple.
        
        Args:
            position: Position to validate
            name: Name of the parameter for error messages
            
        Returns:
            Validated position tuple
            
        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(position, (tuple, list)):
            raise ValidationError(f"{name} must be a tuple or list, got: {type(position)}")
        
        if len(position) != 2:
            raise ValidationError(f"{name} must have exactly 2 elements, got: {len(position)}")
        
        try:
            x, y = float(position[0]), float(position[1])
        except (ValueError, TypeError):
            raise ValidationError(f"{name} coordinates must be numbers, got: {position}")
        
        if x < 0 or y < 0:
            raise ValidationError(f"{name} coordinates must be non-negative, got: ({x}, {y})")
        
        return (x, y)
    
    @staticmethod
    def validate_page_order(order: List[int], max_pages: int) -> List[int]:
        """Validate page order for reordering.
        
        Args:
            order: List of page numbers
            max_pages: Maximum number of pages
            
        Returns:
            Validated page order
            
        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(order, list):
            raise ValidationError(f"Page order must be a list, got: {type(order)}")
        
        if len(order) != max_pages:
            raise ValidationError(f"Page order must contain exactly {max_pages} page numbers, got: {len(order)}")
        
        if not all(isinstance(p, int) for p in order):
            raise ValidationError("All page numbers must be integers")
        
        if set(order) != set(range(max_pages)):
            raise ValidationError(f"Page order must contain each page number from 0 to {max_pages-1} exactly once")
        
        return order
    
    @staticmethod
    def validate_text_input(text: Any, name: str = "text", allow_empty: bool = False) -> str:
        """Validate text input.
        
        Args:
            text: Text to validate
            name: Name of the parameter for error messages
            allow_empty: Whether empty text is allowed
            
        Returns:
            Validated text
            
        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(text, str):
            raise ValidationError(f"{name} must be a string, got: {type(text)}")
        
        if not allow_empty and not text.strip():
            raise ValidationError(f"{name} cannot be empty")
        
        return text.strip()


def validate_and_execute(validation_func: Callable, error_message: str = None):
    """Decorator to validate parameters before executing function.
    
    Args:
        validation_func: Function that validates parameters
        error_message: Custom error message
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Extract the first argument (usually self) and validate the rest
                validation_func(*args[1:], **kwargs)
                return func(*args, **kwargs)
            except Exception as e:
                logger = get_logger(func.__module__)
                error_msg = error_message or f"Validation failed for {func.__name__}: {e}"
                logger.error(error_msg)
                raise ValidationError(error_msg) from e
        return wrapper
    return decorator


def handle_pdf_errors(func):
    """Decorator to handle PDF-related errors consistently.
    
    Args:
        func: Function to wrap
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        
        try:
            return func(*args, **kwargs)
        except ValidationError:
            # Re-raise validation errors as-is
            raise
        except PDFException:
            # Re-raise PDF exceptions as-is
            raise
        except FileNotFoundError as e:
            error_msg = f"File not found: {e}"
            logger.error(error_msg)
            raise ValidationError(error_msg) from e
        except PermissionError as e:
            error_msg = f"Permission denied: {e}"
            logger.error(error_msg)
            raise ValidationError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error in {func.__name__}: {e}"
            logger.error(error_msg)
            raise ProcessingError(error_msg) from e
    
    return wrapper


class ErrorCollector:
    """Collects and manages multiple validation errors."""
    
    def __init__(self):
        """Initialize error collector."""
        self.errors = []
        self.warnings = []
        self.logger = get_logger("error_collector")
    
    def add_error(self, message: str, field: str = None):
        """Add an error.
        
        Args:
            message: Error message
            field: Related field name (optional)
        """
        error = {"message": message, "field": field}
        self.errors.append(error)
        self.logger.error(f"Validation error: {message}" + (f" (field: {field})" if field else ""))
    
    def add_warning(self, message: str, field: str = None):
        """Add a warning.
        
        Args:
            message: Warning message
            field: Related field name (optional)
        """
        warning = {"message": message, "field": field}
        self.warnings.append(warning)
        self.logger.warning(f"Validation warning: {message}" + (f" (field: {field})" if field else ""))
    
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0
    
    def get_errors(self) -> List[Dict[str, str]]:
        """Get all errors."""
        return self.errors.copy()
    
    def get_warnings(self) -> List[Dict[str, str]]:
        """Get all warnings."""
        return self.warnings.copy()
    
    def raise_if_errors(self):
        """Raise ValidationError if there are any errors."""
        if self.has_errors():
            error_messages = [error["message"] for error in self.errors]
            raise ValidationError(f"Validation failed: {'; '.join(error_messages)}")
    
    def clear(self):
        """Clear all errors and warnings."""
        self.errors.clear()
        self.warnings.clear()
        self.logger.debug("Cleared all errors and warnings")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of collected issues.
        
        Returns:
            Summary dictionary
        """
        return {
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": self.get_errors(),
            "warnings": self.get_warnings()
        }