# PDF Editor

A comprehensive PDF editing tool with dark mode conversion and advanced editing capabilities.

## Features

- **Dark Mode Conversion**: Convert PDFs to dark theme (black background, white text)
- **Page Manipulation**: Rotate, delete, reorder pages
- **Text Operations**: Add, replace, highlight text
- **Image Operations**: Insert and manipulate images
- **Batch Processing**: Process multiple files
- **Rich CLI**: Beautiful command-line interface with progress bars
- **Configuration Management**: Flexible YAML-based configuration

## Quick Start

### Installation

1. **Install system dependencies:**

**macOS:**
```bash
brew install poppler
```

**Ubuntu/Debian:**
```bash
sudo apt-get install poppler-utils
```

**Windows:**
Download and install poppler from [poppler releases](https://github.com/osber/poppler-windows/releases)

2. **Install Python dependencies:**
```bash
pip install -r requirements.txt
pip install -e .
```

### Basic Usage

#### Dark Mode Conversion
```bash
python main.py dark-mode input.pdf output_dark.pdf --dpi 300 --quality 95
```

#### Page Rotation
```bash
python main.py rotate input.pdf output.pdf --page 0 --angle 90
```

#### Add Text
```bash
python main.py add-text input.pdf output.pdf --page 0 --text "Hello World" --x 100 --y 100
```

#### Delete Pages
```bash
python main.py delete-pages input.pdf output.pdf --pages "0,2,5"
```

#### Document Info
```bash
python main.py info input.pdf
```

#### Configuration
```bash
python main.py config-show
python main.py config-set dpi 200
```

### Legacy Usage (Backward Compatible)

For simple dark mode conversion, you can still use the original command:
```bash
python init.py input.pdf output_dark.pdf
```

## Project Structure

```
darker-pdf/
├── src/pdf_editor/          # Main package
│   ├── core/               # Core classes and abstractions
│   ├── operations/         # PDF editing operations
│   ├── cli/               # Command-line interface
│   ├── utils/             # Utilities (logging, validation)
│   └── config/            # Configuration management
├── tests/                 # Test suite
├── docs/                  # Documentation
├── examples/              # Usage examples
└── init.py               # Legacy dark mode converter
```

## Development

### Running Tests
```bash
pytest
```

### Code Quality
```bash
black src/ tests/
ruff check src/ tests/
mypy src/
```

## Configuration

The tool uses YAML configuration files. Create `~/.pdf_editor_config.yaml`:

```yaml
dpi: 300
quality: 95
compression: true
output_dir: "./output"
backup_enabled: true
log_level: "INFO"
```

## Roadmap

See [docs/roadmap.md](docs/roadmap.md) for the complete development plan.

### Phase 1: Foundation ✅
- [x] Modular project structure
- [x] Configuration management
- [x] Logging system
- [x] Rich CLI interface
- [x] Error handling and validation

### Phase 2: Basic Editing 🚧
- [ ] Enhanced text operations
- [ ] Advanced page manipulation
- [ ] Image processing
- [ ] Batch operations

### Phase 3: Advanced Features 📋
- [ ] OCR integration
- [ ] Form operations
- [ ] Security features
- [ ] Annotation system

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.
