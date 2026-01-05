"""Logging system for PDF Editor."""

import logging
import os
import sys
from pathlib import Path
from typing import Optional
from rich.logging import RichHandler
from rich.console import Console

from ..config.manager import config_manager


class LoggerManager:
    """Manages logging configuration and provides logger instances."""
    
    def __init__(self):
        """Initialize logger manager."""
        self._loggers = {}
        self._configured = False
        self.console = Console()
    
    def _configure_logging(self) -> None:
        """Configure logging based on configuration."""
        if self._configured:
            return
        
        # Get configuration
        log_level = config_manager.get("log_level", "INFO")
        log_format = config_manager.get("log_format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        log_file = config_manager.get("log_file")
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level.upper()))
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Console handler with rich formatting
        console_handler = RichHandler(
            console=self.console,
            show_time=True,
            show_path=True,
            markup=True,
            rich_tracebacks=True
        )
        console_handler.setLevel(getattr(logging, log_level.upper()))
        root_logger.addHandler(console_handler)
        
        # File handler if configured
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(getattr(logging, log_level.upper()))
            file_handler.setFormatter(logging.Formatter(log_format))
            root_logger.addHandler(file_handler)
        
        self._configured = True
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger instance with the given name."""
        if not self._configured:
            self._configure_logging()
        
        if name not in self._loggers:
            self._loggers[name] = logging.getLogger(name)
        
        return self._loggers[name]
    
    def set_level(self, level: str) -> None:
        """Set logging level for all loggers."""
        log_level = getattr(logging, level.upper(), logging.INFO)
        logging.getLogger().setLevel(log_level)
        
        for handler in logging.getLogger().handlers:
            handler.setLevel(log_level)
    
    def add_file_handler(self, log_file: str, level: str = "INFO") -> None:
        """Add a file handler to the root logger."""
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
        
        formatter = logging.Formatter(
            config_manager.get("log_format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        file_handler.setFormatter(formatter)
        
        logging.getLogger().addHandler(file_handler)


# Global logger manager instance
logger_manager = LoggerManager()


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logger_manager.get_logger(name)


def setup_logging(level: Optional[str] = None, log_file: Optional[str] = None) -> None:
    """Setup logging with optional level and file override."""
    if level:
        logger_manager.set_level(level)
    
    if log_file:
        logger_manager.add_file_handler(log_file)


class ProgressLogger:
    """Logger for tracking progress of operations."""
    
    def __init__(self, logger: logging.Logger, total: int, description: str = "Processing"):
        """Initialize progress logger."""
        self.logger = logger
        self.total = total
        self.current = 0
        self.description = description
        self.last_percentage = -1
    
    def update(self, increment: int = 1, item: Optional[str] = None) -> None:
        """Update progress."""
        self.current += increment
        percentage = (self.current / self.total) * 100
        
        # Log every 10% or for specific items
        if int(percentage) // 10 > self.last_percentage // 10 or item:
            if item:
                self.logger.info(f"{self.description}: {item} ({self.current}/{self.total}, {percentage:.1f}%)")
            else:
                self.logger.info(f"{self.description}: {self.current}/{self.total} ({percentage:.1f}%)")
            self.last_percentage = percentage
    
    def finish(self) -> None:
        """Mark progress as finished."""
        self.logger.info(f"{self.description}: Complete ({self.total}/{self.total}, 100.0%)")
    
    def error(self, message: str) -> None:
        """Log an error during progress."""
        self.logger.error(f"{self.description} Error: {message}")