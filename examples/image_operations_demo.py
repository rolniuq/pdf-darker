#!/usr/bin/env python3
"""
Demonstration of image operations functionality.
This script shows how to use the image editing features of the PDF editor.
"""

import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pdf_editor.core.document import PDFDocument
from pdf_editor.core.manager import OperationManager
from pdf_editor.operations.image_operations import (
    AddImageOperation,
    ResizeImageOperation,
    CropImageOperation,
    ImageFilterOperation,
    AddWatermarkOperation,
    AddImageWatermarkOperation
)

def demonstrate_image_operations():
    """Demonstrate various image operations on a PDF."""
    
    print("🔧 PDF Image Operations Demo")
    print("=" * 40)
    
    # Check for sample files
    input_pdf = Path("sample_document.pdf")
    sample_image = Path("sample_image.png")  # You should provide this
    
    if not input_pdf.exists():
        print(f"❌ Sample PDF not found: {input_pdf}")
        print("Please create or provide a sample PDF file to test with.")
        return
    
    try:
        # Load the PDF document
        doc = PDFDocument(input_pdf)
        print(f"✅ Loaded PDF: {input_pdf.name}")
        print(f"📄 Pages: {doc.page_count}")
        
        # Create operation manager
        manager = OperationManager()
        
        # Example 1: Add an image (if we have one)
        if sample_image.exists():
            print("\n1️⃣ Adding image to page 0...")
            add_image_op = AddImageOperation(
                page_number=0,
                image_path=sample_image,
                position=(100, 100),
                width=200,
                height=150
            )
            manager.add_operation(add_image_op)
        else:
            print("\n1️⃣ ⚠️ Skipping image addition - no sample image found")
        
        # Example 2: Add text watermark
        print("2️⃣ Adding text watermark...")
        watermark_op = AddWatermarkOperation(
            watermark_text="CONFIDENTIAL",
            page_numbers=[0],  # Only first page
            font_size=48,
            opacity=0.3,
            rotation=45,
            color=(0.8, 0.8, 0.8),  # Light gray
            position="center"
        )
        manager.add_operation(watermark_op)
        
        # Example 3: Add image watermark (if we have an image)
        if sample_image.exists():
            print("3️⃣ Adding image watermark...")
            img_watermark_op = AddImageWatermarkOperation(
                watermark_image_path=str(sample_image),
                page_numbers=[0],
                opacity=0.2,
                scale=0.3,
                position="bottom_right"
            )
            manager.add_operation(img_watermark_op)
        else:
            print("3️⃣ ⚠️ Skipping image watermark - no sample image found")
        
        # Example 4: Apply image filters (to existing images in PDF)
        if doc.page_count > 0:
            print("4️⃣ Applying image filters...")
            # Try to apply brightness filter to first image if it exists
            page = doc.get_page(0)
            images = page._page.get_images()
            
            if images:
                filter_op = ImageFilterOperation(
                    page_number=0,
                    image_index=0,
                    filter_type="brightness",
                    intensity=1.2
                )
                manager.add_operation(filter_op)
                
                # Add contrast filter as well
                contrast_op = ImageFilterOperation(
                    page_number=0,
                    image_index=0,
                    filter_type="contrast",
                    intensity=1.1
                )
                manager.add_operation(contrast_op)
            else:
                print("4️⃣ ⚠️ No images found in PDF to apply filters")
        
        # Example 5: Resize image (if images exist)
        if doc.page_count > 0:
            page = doc.get_page(0)
            images = page._page.get_images()
            
            if images:
                print("5️⃣ Resizing image...")
                resize_op = ResizeImageOperation(
                    page_number=0,
                    image_index=0,
                    width=300,
                    height=200,
                    maintain_aspect=True
                )
                manager.add_operation(resize_op)
        
        # Execute all operations
        print("\n🚀 Executing operations...")
        results = manager.execute_operations(doc)
        
        # Show results
        summary = manager.get_results_summary()
        print(f"\n📊 Results Summary:")
        print(f"   Total operations: {summary['total']}")
        print(f"   Successful: {summary['successful']}")
        print(f"   Failed: {summary['failed']}")
        print(f"   Success rate: {summary['success_rate']:.1f}%")
        
        # Save the modified document
        if doc.is_modified:
            output_path = input_pdf.parent / f"modified_images_{input_pdf.name}"
            doc.save(output_path)
            print(f"💾 Saved modified PDF to: {output_path}")
        else:
            print("ℹ️ No modifications were made to the document")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    print("\n✨ Image operations demo completed!")
    return True

def create_sample_image():
    """Create a simple sample image for testing."""
    try:
        from PIL import Image, ImageDraw
        
        # Create a simple test image
        img = Image.new('RGB', (200, 150), color='lightblue')
        draw = ImageDraw.Draw(img)
        
        # Draw some shapes
        draw.rectangle([20, 20, 180, 130], outline='black', width=2)
        draw.ellipse([50, 50, 150, 100], fill='red', outline='black', width=2)
        draw.text((70, 70), "TEST", fill='white')
        
        img.save("sample_image.png")
        print("✅ Created sample image: sample_image.png")
        return True
        
    except ImportError:
        print("⚠️ PIL not available, cannot create sample image")
        return False
    except Exception as e:
        print(f"❌ Error creating sample image: {e}")
        return False

if __name__ == "__main__":
    # Create sample image if it doesn't exist
    if not Path("sample_image.png").exists():
        create_sample_image()
    
    demonstrate_image_operations()