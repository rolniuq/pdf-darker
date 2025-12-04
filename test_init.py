import os
import tempfile
from PIL import Image
from init import invert_image, convert_pdf_to_dark


def test_invert_image_white_to_black():
    """Test that a white image becomes black after inversion."""
    white_image = Image.new("RGB", (100, 100), color=(255, 255, 255))
    inverted = invert_image(white_image)

    # Check that the result is black
    pixels = list(inverted.getdata())
    assert all(pixel == (0, 0, 0) for pixel in pixels)


def test_invert_image_black_to_white():
    """Test that a black image becomes white after inversion."""
    black_image = Image.new("RGB", (100, 100), color=(0, 0, 0))
    inverted = invert_image(black_image)

    # Check that the result is white
    pixels = list(inverted.getdata())
    assert all(pixel == (255, 255, 255) for pixel in pixels)


def test_invert_image_preserves_size():
    """Test that image dimensions are preserved after inversion."""
    image = Image.new("RGB", (200, 150), color=(128, 128, 128))
    inverted = invert_image(image)

    assert inverted.size == (200, 150)


def test_invert_image_rgba_to_rgb():
    """Test that RGBA images are converted to RGB."""
    rgba_image = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
    inverted = invert_image(rgba_image)

    assert inverted.mode == "RGB"


def test_convert_pdf_creates_output_file():
    """Test that convert_pdf_to_dark creates an output file."""
    # Create a simple test PDF
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a simple image and save as PDF
        input_pdf = os.path.join(tmpdir, "test_input.pdf")
        output_pdf = os.path.join(tmpdir, "test_output.pdf")

        # Create a white image and save as PDF
        img = Image.new("RGB", (100, 100), color=(255, 255, 255))
        img.save(input_pdf, "PDF")

        # Convert to dark mode
        convert_pdf_to_dark(input_pdf, output_pdf, dpi=72, verbose=False)

        # Check output file exists
        assert os.path.exists(output_pdf)
        assert os.path.getsize(output_pdf) > 0
