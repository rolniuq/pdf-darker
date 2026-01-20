"""Main PDF editor class."""

from typing import List, Dict, Any, Optional, Union
from pathlib import Path

from .base import (
    OperationManager, PluginManager,
    BaseOperation, PDFException
)
from .document import PDFDocument
from ..config.manager import config_manager
from ..utils.logging import get_logger


class PDFEditor:
    """Main PDF editor class that coordinates all operations."""
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize PDF editor.
        
        Args:
            config_file: Optional configuration file path
        """
        if config_file:
            from ..config.manager import ConfigManager
            global config_manager
            config_manager = ConfigManager(config_file)
        
        self.logger = get_logger("pdf_editor")
        self.operation_manager = OperationManager()
        self.plugin_manager = PluginManager()
        self.current_document: Optional[PDFDocument] = None
        
        self.logger.info("PDF Editor initialized")
    
    def load_document(self, file_path: Union[str, Path]) -> PDFDocument:
        """Load a PDF document.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Loaded PDF document
            
        Raises:
            PDFException: If document cannot be loaded
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise PDFException(f"File not found: {file_path}")
        
        if not file_path.suffix.lower() == ".pdf":
            raise PDFException(f"File is not a PDF: {file_path}")
        
        try:
            self.current_document = PDFDocument(file_path)
            self.logger.info(f"Loaded document: {file_path}")
            return self.current_document
            
        except Exception as e:
            raise PDFException(f"Failed to load document {file_path}: {e}")
    
    def save_document(self, file_path: Optional[Union[str, Path]] = None) -> bool:
        """Save the current document.
        
        Args:
            file_path: Optional output path. If None, saves to original location
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            PDFException: If no document is loaded or save fails
        """
        if not self.current_document:
            raise PDFException("No document loaded")
        
        if not self.current_document.is_modified:
            self.logger.info("Document not modified, skipping save")
            return True
        
        # Determine output path
        if file_path:
            output_path = Path(file_path)
        else:
            # Create backup if enabled
            if config_manager.get("backup_enabled"):
                self._create_backup()
            output_path = self.current_document.file_path
        
        try:
            # Save the document using the document's save method
            self.current_document.save(output_path)
            self.logger.info(f"Document saved to: {output_path}")
            return True
            
        except Exception as e:
            raise PDFException(f"Failed to save document: {e}")
    
    def add_operation(self, operation: BaseOperation) -> None:
        """Add an operation to the queue.
        
        Args:
            operation: Operation to add
        """
        self.operation_manager.add_operation(operation)
    
    def execute_operations(self) -> Dict[str, Any]:
        """Execute all queued operations.
        
        Returns:
            Operation results summary
        """
        if not self.current_document:
            raise PDFException("No document loaded")
        
        # Actually execute the operations
        self.operation_manager.execute_operations(self.current_document)
        
        # Get the results summary
        summary = self.operation_manager.get_results_summary()
        
        self.logger.info(f"Operations completed: {summary['successful']}/{summary['total']} successful")
        return summary
    
    def clear_operations(self) -> None:
        """Clear all pending operations."""
        self.operation_manager.clear_operations()
        self.logger.debug("Cleared all operations")
    
    def register_plugin(self, plugin) -> None:
        """Register a plugin.
        
        Args:
            plugin: Plugin to register
        """
        self.plugin_manager.register_plugin(plugin)
    
    def get_document_info(self) -> Dict[str, Any]:
        """Get information about the current document.
        
        Returns:
            Document information
        """
        if not self.current_document:
            return {}
        
        return {
            "file_path": str(self.current_document.file_path),
            "page_count": self.current_document.page_count,
            "metadata": self.current_document.metadata,
            "is_modified": self.current_document.is_modified
        }
    
    def get_pending_operations(self) -> List[Dict[str, Any]]:
        """Get list of pending operations.
        
        Returns:
            List of pending operations
        """
        return [
            {
                "type": op.operation_type.value,
                "parameters": op.parameters
            }
            for op in self.operation_manager.operations
        ]
    
    def _create_backup(self) -> None:
        """Create a backup of the current document."""
        if not self.current_document:
            return
        
        backup_dir = Path(config_manager.get("backup_dir", "./backups"))
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Create backup filename with timestamp
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{self.current_document.file_path.stem}_{timestamp}{self.current_document.file_path.suffix}"
        backup_path = backup_dir / backup_name
        
        try:
            # Copy file to backup location
            import shutil
            shutil.copy2(self.current_document.file_path, backup_path)
            self.logger.info(f"Created backup: {backup_path}")
            
        except Exception as e:
            self.logger.warning(f"Failed to create backup: {e}")
    
    def close_document(self) -> None:
        """Close the current document."""
        if self.current_document:
            if self.current_document.is_modified:
                self.logger.warning("Closing modified document without saving")
            
            self.current_document = None
            self.logger.info("Document closed")