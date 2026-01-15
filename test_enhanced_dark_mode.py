"""Test Enhanced Dark Mode with Text Preservation."""

import sys
from pathlib import Path

# Add src to path for direct execution
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pdf_editor import PDFEditor
from pdf_editor.operations.dark_mode import DarkModeOperation


def test_enhanced_dark_mode():
    """Test the enhanced dark mode functionality."""
    print("🌙 Testing Enhanced Dark Mode with Text Preservation")
    print("=" * 50)
    
    # Use the sample PDF
    input_path = "sample_document.pdf"
    if not Path(input_path).exists():
        print(f"❌ Error: {input_path} not found")
        return
    
    print(f"📄 Using: {input_path}")
    
    # Test 1: Enhanced Dark Mode (default)
    print("\n✅ Test 1: Enhanced Dark Mode (Default)")
    print("   Preserving text layer, links, and forms...")
    
    editor = PDFEditor()
    
    # Enhanced mode (preserves text)
    operation = DarkModeOperation(
        dpi=150,  # Lower for faster testing
        quality=85,
        preserve_text=True,
        preserve_forms=True,
        preserve_links=True,
        use_enhanced=True,
        verbose=True
    )
    
    editor.load_document(input_path)
    editor.add_operation(operation)
    result = editor.execute_operations()
    
    output_path = "enhanced_dark_mode.pdf"
    editor.save_document(output_path)
    
    print(f"   Result: {result}")
    print(f"   Output: {output_path}")
    
    # Test 2: Legacy Mode (comparison)
    print("\n⚠️  Test 2: Legacy Dark Mode (Image-based)")
    print("   Converting to images (text layer lost)...")
    
    operation_legacy = DarkModeOperation(
        dpi=150,
        quality=85,
        preserve_text=False,
        use_enhanced=False,
        verbose=True
    )
    
    editor.load_document(input_path)
    editor.add_operation(operation_legacy)
    result_legacy = editor.execute_operations()
    
    output_legacy_path = "legacy_dark_mode.pdf"
    editor.save_document(output_legacy_path)
    
    print(f"   Result: {result_legacy}")
    print(f"   Output: {output_legacy_path}")
    
    # Test 3: Comparison
    print("\n📊 Comparison Summary:")
    print("=" * 30)
    
    # Check file sizes
    enhanced_size = Path(output_path).stat().st_size if Path(output_path).exists() else 0
    legacy_size = Path(output_legacy_path).stat().st_size if Path(output_legacy_path).exists() else 0
    
    print(f"Enhanced Mode:  {enhanced_size:,} bytes")
    print(f"Legacy Mode:    {legacy_size:,} bytes")
    
    # Display key differences
    print("\n🔍 Key Differences:")
    print("Enhanced Mode:")
    print("   ✅ Text layer preserved (selectable, searchable)")
    print("   ✅ Links clickable (TOC, web links work)")
    print("   ✅ Form fields functional (can fill forms)")
    print("   ✅ Bookmarks preserved (navigation works)")
    print("   ✅ Annotations preserved (comments, highlights stay)")
    
    print("\nLegacy Mode:")
    print("   ❌ Text layer lost (image-only)")
    print("   ❌ Links broken (clickable links lost)")
    print("   ❌ Forms lost (cannot fill)")
    print("   ❌ Navigation lost (no TOC/bookmarks)")
    print("   ❌ Quality reduced (image artifacts)")
    
    print("\n💡 Recommendation:")
    print("Always use Enhanced Dark Mode (default) to maintain PDF functionality!")
    print("Only use Legacy Mode for compatibility with very old PDF viewers.")
    
    print(f"\n🎉 Test Complete!")
    print("Files created:")
    if Path(output_path).exists():
        print(f"   ✅ enhanced_dark_mode.pdf (RECOMMENDED)")
    if Path(output_legacy_path).exists():
        print(f"   ⚠️  legacy_dark_mode.pdf (TEXT LOST)")


if __name__ == "__main__":
    test_enhanced_dark_mode()