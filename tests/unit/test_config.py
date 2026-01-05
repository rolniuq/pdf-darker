"""Unit tests for configuration management."""

import pytest
import yaml
from pathlib import Path

from src.pdf_editor.config.manager import ConfigManager, PDFConfig


class TestPDFConfig:
    """Test PDFConfig dataclass."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = PDFConfig()
        assert config.dpi == 300
        assert config.quality == 95
        assert config.compression is True
        assert config.output_dir == "./output"
        assert config.backup_enabled is True
        assert config.parallel_processing is True
        assert config.max_workers == 4
        assert config.ocr_enabled is False
        assert config.ocr_language == "eng"
        assert config.log_level == "INFO"
    
    def test_config_customization(self):
        """Test configuration customization."""
        config = PDFConfig(dpi=200, log_level="DEBUG", ocr_enabled=True)
        assert config.dpi == 200
        assert config.log_level == "DEBUG"
        assert config.ocr_enabled is True


class TestConfigManager:
    """Test ConfigManager class."""
    
    def test_config_creation_with_file(self, temp_dir):
        """Test creating config manager with specific file."""
        config_file = temp_dir / "test_config.yaml"
        manager = ConfigManager(str(config_file))
        assert manager.config_file == str(config_file)
        assert config_file.exists()
    
    def test_config_loading_from_existing_file(self, temp_dir):
        """Test loading configuration from existing file."""
        config_file = temp_dir / "existing_config.yaml"
        
        # Create config file with custom settings
        test_config = {
            "dpi": 200,
            "log_level": "DEBUG",
            "ocr_enabled": True
        }
        
        with open(config_file, "w") as f:
            yaml.dump(test_config, f)
        
        manager = ConfigManager(str(config_file))
        assert manager.config.dpi == 200
        assert manager.config.log_level == "DEBUG"
        assert manager.config.ocr_enabled is True
    
    def test_config_get_and_set(self, temp_dir):
        """Test getting and setting configuration values."""
        manager = ConfigManager(str(temp_dir / "test_config.yaml"))
        
        # Test get
        assert manager.get("dpi") == 300
        assert manager.get("nonexistent", "default") == "default"
        
        # Test set
        manager.set("dpi", 200)
        assert manager.get("dpi") == 200
        
        # Test set invalid key
        with pytest.raises(ValueError):
            manager.set("invalid_key", "value")
    
    def test_config_update(self, temp_dir):
        """Test updating multiple configuration values."""
        manager = ConfigManager(str(temp_dir / "test_config.yaml"))
        
        manager.update(dpi=200, quality=85, log_level="DEBUG")
        
        assert manager.config.dpi == 200
        assert manager.config.quality == 85
        assert manager.config.log_level == "DEBUG"
    
    def test_config_reset(self, temp_dir):
        """Test resetting configuration to defaults."""
        manager = ConfigManager(str(temp_dir / "test_config.yaml"))
        
        # Modify some values
        manager.set("dpi", 200)
        manager.set("log_level", "DEBUG")
        
        # Reset
        manager.reset()
        
        # Check defaults are restored
        assert manager.config.dpi == 300
        assert manager.config.log_level == "INFO"