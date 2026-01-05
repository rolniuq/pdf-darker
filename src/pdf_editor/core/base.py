"""Base classes and interfaces for PDF editing operations."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from enum import Enum

from ..utils.logging import get_logger


class OperationType(Enum):
    """Types of PDF operations."""
    
    # Text operations
    ADD_TEXT = "add_text"
    REPLACE_TEXT = "replace_text"
    DELETE_TEXT = "delete_text"
    HIGHLIGHT_TEXT = "highlight_text"
    
    # Page operations
    ROTATE_PAGE = "rotate_page"
    DELETE_PAGE = "delete_page"
    REORDER_PAGES = "reorder_pages"
    MERGE_PAGES = "merge_pages"
    SPLIT_PAGES = "split_pages"
    
    # Image operations
    ADD_IMAGE = "add_image"
    REPLACE_IMAGE = "replace_image"
    DELETE_IMAGE = "delete_image"
    CROP_IMAGE = "crop_image"
    
    # Annotation operations
    ADD_ANNOTATION = "add_annotation"
    DELETE_ANNOTATION = "delete_annotation"
    
    # Document operations
    COMPRESS = "compress"
    ENCRYPT = "encrypt"
    DECRYPT = "decrypt"
    ADD_WATERMARK = "add_watermark"
    
    # Special operations
    DARK_MODE = "dark_mode"


class OperationResult(Enum):
    """Result of an operation."""
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    SKIPPED = "skipped"


class PDFException(Exception):
    """Base exception for PDF operations."""
    
    def __init__(self, message: str, operation: Optional[OperationType] = None, details: Optional[Dict] = None):
        super().__init__(message)
        self.operation = operation
        self.details = details or {}


class ValidationError(PDFException):
    """Exception raised for validation errors."""


class ProcessingError(PDFException):
    """Exception raised during PDF processing."""


class BaseOperation(ABC):
    """Base class for all PDF operations."""
    
    def __init__(self, operation_type: Union[OperationType, str]):
        """Initialize operation.
        
        Args:
            operation_type: Type of operation (Enum or string)
        """
        # Handle both Enum and string operation types
        if isinstance(operation_type, str):
            self.operation_type = OperationType(operation_type)
        else:
            self.operation_type = operation_type
        
        self.logger = get_logger(f"operation.{self.operation_type.value}")
        self.parameters = {}
    
    @abstractmethod
    def validate(self, document: 'PDFDocument') -> bool:
        """Validate operation parameters.
        
        Args:
            document: PDF document to validate against
            
        Returns:
            True if valid, False otherwise
        """
        pass
    
    @abstractmethod
    def execute(self, document: 'PDFDocument') -> OperationResult:
        """Execute the operation.
        
        Args:
            document: PDF document to operate on
            
        Returns:
            Operation result
        """
        pass
    
    def set_parameter(self, key: str, value: Any) -> None:
        """Set operation parameter.
        
        Args:
            key: Parameter name
            value: Parameter value
        """
        self.parameters[key] = value
    
    def get_parameter(self, key: str, default: Any = None) -> Any:
        """Get operation parameter.
        
        Args:
            key: Parameter name
            default: Default value if not found
            
        Returns:
            Parameter value
        """
        return self.parameters.get(key, default)


class PDFDocument:
    """Represents a PDF document."""
    
    def __init__(self, file_path: Union[str, Path]):
        """Initialize PDF document.
        
        Args:
            file_path: Path to PDF file
        """
        self.file_path = Path(file_path)
        self.logger = get_logger("document")
        self._metadata = {}
        self._pages = []
        self._is_modified = False
        self._backup_created = False
    
    @property
    def is_modified(self) -> bool:
        """Check if document has been modified."""
        return self._is_modified
    
    @property
    def page_count(self) -> int:
        """Get number of pages."""
        return len(self._pages)
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """Get document metadata."""
        return self._metadata.copy()
    
    def mark_modified(self) -> None:
        """Mark document as modified."""
        self._is_modified = True
    
    def clear_modified_flag(self) -> None:
        """Clear modified flag."""
        self._is_modified = False


class OperationManager:
    """Manages and executes PDF operations."""
    
    def __init__(self):
        """Initialize operation manager."""
        self.logger = get_logger("operation_manager")
        self.operations: List[BaseOperation] = []
        self.results: List[Dict[str, Any]] = []
    
    def add_operation(self, operation: BaseOperation) -> None:
        """Add an operation to the queue.
        
        Args:
            operation: Operation to add
        """
        self.operations.append(operation)
        self.logger.debug(f"Added operation: {operation.operation_type.value}")
    
    def clear_operations(self) -> None:
        """Clear all operations."""
        self.operations.clear()
        self.results.clear()
        self.logger.debug("Cleared all operations")
    
    def execute_operations(self, document: PDFDocument) -> List[Dict[str, Any]]:
        """Execute all operations on document.
        
        Args:
            document: PDF document to operate on
            
        Returns:
            List of operation results
        """
        self.results = []
        
        for i, operation in enumerate(self.operations):
            self.logger.info(f"Executing operation {i+1}/{len(self.operations)}: {operation.operation_type.value}")
            
            result = {
                "operation": operation.operation_type,
                "index": i,
                "success": False,
                "message": "",
                "details": {}
            }
            
            try:
                # Validate operation
                if not operation.validate(document):
                    raise ValidationError(f"Operation validation failed: {operation.operation_type.value}")
                
                # Execute operation
                operation_result = operation.execute(document)
                
                result["success"] = operation_result == OperationResult.SUCCESS
                result["message"] = f"Operation completed: {operation_result.value}"
                
                self.logger.info(f"Operation {i+1} completed: {operation_result.value}")
                
            except Exception as e:
                result["success"] = False
                result["message"] = str(e)
                result["details"]["error_type"] = type(e).__name__
                
                self.logger.error(f"Operation {i+1} failed: {e}")
            
            self.results.append(result)
        
        return self.results
    
    def get_results_summary(self) -> Dict[str, Any]:
        """Get summary of operation results.
        
        Returns:
            Results summary
        """
        if not self.results:
            return {"total": 0, "successful": 0, "failed": 0, "success_rate": 0.0}
        
        total = len(self.results)
        successful = sum(1 for r in self.results if r["success"])
        failed = total - successful
        
        return {
            "total": total,
            "successful": successful,
            "failed": failed,
            "success_rate": (successful / total) * 100 if total > 0 else 0.0
        }


class Plugin(ABC):
    """Base class for plugins."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name."""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Plugin description."""
        pass
    
    @abstractmethod
    def get_operations(self) -> List[type]:
        """Get operations provided by this plugin."""
        pass


class PluginManager:
    """Manages plugins and their operations."""
    
    def __init__(self):
        """Initialize plugin manager."""
        self.logger = get_logger("plugin_manager")
        self.plugins: Dict[str, Plugin] = {}
        self.operations: Dict[str, type] = {}
    
    def register_plugin(self, plugin: Plugin) -> None:
        """Register a plugin.
        
        Args:
            plugin: Plugin to register
        """
        self.plugins[plugin.name] = plugin
        
        # Register plugin operations
        for operation_class in plugin.get_operations():
            operation_name = operation_class.__name__
            self.operations[operation_name] = operation_class
        
        self.logger.info(f"Registered plugin: {plugin.name} v{plugin.version}")
    
    def get_plugin(self, name: str) -> Optional[Plugin]:
        """Get plugin by name.
        
        Args:
            name: Plugin name
            
        Returns:
            Plugin instance or None
        """
        return self.plugins.get(name)
    
    def get_operation_class(self, name: str) -> Optional[type]:
        """Get operation class by name.
        
        Args:
            name: Operation class name
            
        Returns:
            Operation class or None
        """
        return self.operations.get(name)
    
    def list_plugins(self) -> List[Dict[str, str]]:
        """List all registered plugins.
        
        Returns:
            List of plugin info
        """
        return [
            {
                "name": plugin.name,
                "version": plugin.version,
                "description": plugin.description
            }
            for plugin in self.plugins.values()
        ]