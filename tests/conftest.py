"""Test configuration and fixtures for PDF Editor tests."""

import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Generator

from src.pdf_editor.config.manager import ConfigManager, PDFConfig
from src.pdf_editor.utils.logging import get_logger


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def test_config(temp_dir: Path) -> Generator[ConfigManager, None, None]:
    """Create a test configuration manager."""
    config_file = temp_dir / "test_config.yaml"
    config_manager = ConfigManager(str(config_file))
    yield config_manager


@pytest.fixture
def sample_pdf_path(temp_dir: Path) -> Path:
    """Path to a sample PDF file for testing."""
    # This would ideally create a real PDF file
    # For now, just return the path where it would be
    return temp_dir / "sample.pdf"


@pytest.fixture
def logger():
    """Get a test logger."""
    return get_logger("test")


@pytest.fixture
def pdf_config() -> PDFConfig:
    """Create a test PDF configuration."""
    return PDFConfig(
        dpi=150,
        quality=85,
        output_dir="./test_output",
        log_level="DEBUG"
    )