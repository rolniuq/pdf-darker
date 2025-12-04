from pdf2image import convert_from_path
from PIL import ImageOps, Image
import sys


def invert_image(image: Image.Image) -> Image.Image:
    """Invert colors of an image."""
    return ImageOps.invert(image.convert("RGB"))


def convert_pdf_to_dark(input_pdf: str, output_pdf: str, dpi: int = 300, verbose: bool = True):
    """Convert a PDF from light mode to dark mode."""
    if verbose:
        print(f"Converting {input_pdf} to dark mode...")

    # Convert PDF pages to images (higher DPI = sharper text)
    pages = convert_from_path(input_pdf, dpi=dpi)

    # Invert colors for each page
    inverted_pages = []
    for i, page in enumerate(pages):
        if verbose:
            print(f"Processing page {i + 1}/{len(pages)}...")
        inverted = invert_image(page)
        inverted_pages.append(inverted)

    # Save as PDF
    inverted_pages[0].save(output_pdf, save_all=True, append_images=inverted_pages[1:])
    if verbose:
        print(f"Done! Dark PDF saved to: {output_pdf}")

    return inverted_pages


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python init.py input.pdf output_dark.pdf")
        sys.exit(1)

    input_pdf = sys.argv[1]
    output_pdf = sys.argv[2]
    convert_pdf_to_dark(input_pdf, output_pdf)
