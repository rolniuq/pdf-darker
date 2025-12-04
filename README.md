# Darker PDF

Convert PDFs from white background with black text to dark mode (black background with white text).

## Prerequisites

### System Dependencies

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

### Python Dependencies

```bash
pip install pdf2image Pillow
```

## Usage

```bash
python init.py <input.pdf> <output.pdf>
```

### Example

```bash
python init.py "My Book.pdf" "My Book Dark.pdf"
```

## Notes

- The output PDF contains rasterized pages (text is not selectable)
- Higher DPI (currently 300) produces sharper text but larger file sizes
- Processing time depends on the number of pages
