"""Configuration management for PDF Editor."""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, asdict


@dataclass
class PDFConfig:
    """Configuration settings for PDF processing."""
    
    # PDF processing settings
    dpi: int = 300
    quality: int = 95
    compression: bool = True
    
    # Output settings
    output_dir: str = "./output"
    backup_enabled: bool = True
    backup_dir: str = "./backups"
    
    # Processing settings
    parallel_processing: bool = True
    max_workers: int = 4
    chunk_size: int = 10
    
    # OCR settings
    ocr_enabled: bool = False
    ocr_language: str = "eng"
    ocr_config: Dict[str, Any] = None
    
    # Logging settings
    log_level: str = "INFO"
    log_file: Optional[str] = None
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    def __post_init__(self):
        """Post-initialization setup."""
        if self.ocr_config is None:
            self.ocr_config = {}


class ConfigManager:
    """Manages application configuration."""
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize configuration manager.
        
        Args:
            config_file: Path to configuration file
        """
        self.config_file = config_file or self._get_default_config_file()
        self.config = PDFConfig()
        self._load_config()
    
    def _get_default_config_file(self) -> str:
        """Get default configuration file path."""
        # Check environment variable first
        env_config = os.getenv("PDF_EDITOR_CONFIG")
        if env_config and os.path.exists(env_config):
            return env_config
        
        # Check current directory
        local_config = Path("./pdf_editor_config.yaml")
        if local_config.exists():
            return str(local_config)
        
        # Check home directory
        home_config = Path.home() / ".pdf_editor_config.yaml"
        if home_config.exists():
            return str(home_config)
        
        # Return default path
        return str(Path.home() / ".pdf_editor_config.yaml")
    
    def _load_config(self) -> None:
        """Load configuration from file."""
        if not os.path.exists(self.config_file):
            self._save_config()  # Create default config file
            return
        
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if data:
                    self._update_config_from_dict(data)
        except Exception as e:
            print(f"Warning: Failed to load config file {self.config_file}: {e}")
    
    def _update_config_from_dict(self, data: Dict[str, Any]) -> None:
        """Update configuration from dictionary."""
        for key, value in data.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
    
    def _save_config(self) -> None:
        """Save current configuration to file."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, "w", encoding="utf-8") as f:
                yaml.dump(asdict(self.config), f, default_flow_style=False, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save config file {self.config_file}: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return getattr(self.config, key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        if hasattr(self.config, key):
            setattr(self.config, key, value)
            self._save_config()
        else:
            raise ValueError(f"Unknown configuration key: {key}")
    
    def update(self, **kwargs) -> None:
        """Update multiple configuration values."""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
            else:
                raise ValueError(f"Unknown configuration key: {key}")
        self._save_config()
    
    def reset(self) -> None:
        """Reset configuration to defaults."""
        self.config = PDFConfig()
        self._save_config()


# Global configuration instance
config_manager = ConfigManager()