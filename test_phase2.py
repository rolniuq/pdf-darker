#!/usr/bin/env python3
"""
Simple test to verify Phase 2 functionality works.
This test doesn't require pytest and can be run directly.
"""

import sys
import os
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test that all new operations can be imported."""
    
    print("🔧 Testing imports...")
    
    try:
        # Test text operations imports
        from src.pdf_editor.operations.text_operations import (
            AddTextOperation,
            HighlightTextOperation,
            AddAnnotationOperation,
            AddTextBoxOperation,
            ReplaceTextOperation,
            DeleteTextOperation
        )
        print("✅ Text operations imports successful")
        
        # Test page operations imports
        from src.pdf_editor.operations.page_operations import (
            RotatePageOperation,
            DeletePageOperation,
            ReorderPagesOperation,
            InsertPageOperation,
            ExtractPagesOperation,
            MergeDocumentsOperation,
            SplitDocumentOperation
        )
        print("✅ Page operations imports successful")
        
        # Test image operations imports
        from src.pdf_editor.operations.image_operations import (
            AddImageOperation,
            ResizeImageOperation,
            CropImageOperation,
            ImageFilterOperation,
            AddWatermarkOperation,
            AddImageWatermarkOperation
        )
        print("✅ Image operations imports successful")
        
        # Test CLI imports
        from src.pdf_editor.cli.main import cli
        print("✅ CLI imports successful")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_operation_creation():
    """Test that operations can be created with basic parameters."""
    
    print("\n🔧 Testing operation creation...")
    
    try:
        from src.pdf_editor.operations.text_operations import (
            AddTextOperation,
            HighlightTextOperation,
            AddAnnotationOperation
        )
        
        from src.pdf_editor.operations.page_operations import (
            RotatePageOperation,
            DeletePageOperation
        )
        
        from src.pdf_editor.operations.image_operations import (
            AddImageOperation,
            AddWatermarkOperation
        )
        
        # Test text operation creation
        add_text = AddTextOperation(0, "Test text", (100, 100))
        print("✅ AddTextOperation created successfully")
        
        highlight = HighlightTextOperation("search", (1, 1, 0))
        print("✅ HighlightTextOperation created successfully")
        
        annotate = AddAnnotationOperation(0, (100, 100), "Note text")
        print("✅ AddAnnotationOperation created successfully")
        
        # Test page operation creation
        rotate = RotatePageOperation(0, 90)
        print("✅ RotatePageOperation created successfully")
        
        delete = DeletePageOperation(0)
        print("✅ DeletePageOperation created successfully")
        
        # Test image operation creation
        watermark = AddWatermarkOperation("WATERMARK")
        print("✅ AddWatermarkOperation created successfully")
        
        # Note: AddImageOperation requires a valid image file, so we'll skip that for now
        
        return True
        
    except Exception as e:
        print(f"❌ Operation creation error: {e}")
        return False

def test_cli_help():
    """Test that CLI help works."""
    
    print("\n🔧 Testing CLI help...")
    
    try:
        from src.pdf_editor.cli.main import cli
        
        # Test basic CLI help
        from click.testing import CliRunner
        runner = CliRunner()
        
        result = runner.invoke(cli, ['--help'])
        if result.exit_code == 0:
            print("✅ CLI help command works")
        else:
            print(f"❌ CLI help failed: {result.output}")
            return False
        
        # Test text group help
        result = runner.invoke(cli, ['text', '--help'])
        if result.exit_code == 0:
            print("✅ Text group help works")
        else:
            print(f"❌ Text group help failed: {result.output}")
            return False
        
        # Test pages group help
        result = runner.invoke(cli, ['pages', '--help'])
        if result.exit_code == 0:
            print("✅ Pages group help works")
        else:
            print(f"❌ Pages group help failed: {result.output}")
            return False
        
        # Test images group help
        result = runner.invoke(cli, ['images', '--help'])
        if result.exit_code == 0:
            print("✅ Images group help works")
        else:
            print(f"❌ Images group help failed: {result.output}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ CLI help test error: {e}")
        return False

def main():
    """Run all tests."""
    
    print("🚀 Phase 2 Implementation Test")
    print("=" * 40)
    
    tests = [
        ("Import Test", test_imports),
        ("Operation Creation Test", test_operation_creation),
        ("CLI Help Test", test_cli_help)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name}...")
        try:
            if test_func():
                print(f"✅ {test_name} PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! Phase 2 implementation looks good!")
        return True
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)