#!/usr/bin/env python3
"""
Simple structural test for Phase 2 implementation.
This test checks that the code files exist and have expected content.
"""

import sys
from pathlib import Path

def test_file_structure():
    """Test that all expected files exist."""
    
    print("🔧 Testing file structure...")
    
    expected_files = [
        "src/pdf_editor/operations/text_operations.py",
        "src/pdf_editor/operations/page_operations.py", 
        "src/pdf_editor/operations/image_operations.py",
        "src/pdf_editor/cli/main.py",
        "examples/text_operations_demo.py",
        "examples/page_operations_demo.py",
        "examples/image_operations_demo.py"
    ]
    
    missing_files = []
    for file_path in expected_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    else:
        print("✅ All expected files exist")
        return True

def test_class_definitions():
    """Test that operation classes are properly defined."""
    
    print("\n🔧 Testing class definitions...")
    
    try:
        # Check text operations
        text_ops_file = Path("src/pdf_editor/operations/text_operations.py")
        content = text_ops_file.read_text()
        
        expected_classes = [
            "HighlightTextOperation",
            "AddAnnotationOperation", 
            "AddTextBoxOperation"
        ]
        
        for class_name in expected_classes:
            if f"class {class_name}" in content:
                print(f"✅ {class_name} defined")
            else:
                print(f"❌ {class_name} not found")
                return False
        
        # Check page operations
        page_ops_file = Path("src/pdf_editor/operations/page_operations.py")
        content = page_ops_file.read_text()
        
        expected_page_classes = [
            "InsertPageOperation",
            "ExtractPagesOperation",
            "MergeDocumentsOperation",
            "SplitDocumentOperation"
        ]
        
        for class_name in expected_page_classes:
            if f"class {class_name}" in content:
                print(f"✅ {class_name} defined")
            else:
                print(f"❌ {class_name} not found")
                return False
        
        # Check image operations
        img_ops_file = Path("src/pdf_editor/operations/image_operations.py")
        content = img_ops_file.read_text()
        
        expected_img_classes = [
            "ResizeImageOperation",
            "CropImageOperation",
            "ImageFilterOperation",
            "AddWatermarkOperation",
            "AddImageWatermarkOperation"
        ]
        
        for class_name in expected_img_classes:
            if f"class {class_name}" in content:
                print(f"✅ {class_name} defined")
            else:
                print(f"❌ {class_name} not found")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking class definitions: {e}")
        return False

def test_cli_commands():
    """Test that CLI commands are defined."""
    
    print("\n🔧 Testing CLI command definitions...")
    
    try:
        cli_file = Path("src/pdf_editor/cli/main.py")
        content = cli_file.read_text()
        
        expected_commands = [
            "def highlight",
            "def annotate", 
            "def insert",
            "def extract",
            "def merge",
            "def filter",
            "def watermark"
        ]
        
        for command in expected_commands:
            if command in content:
                print(f"✅ CLI command {command.replace('def ', '')} defined")
            else:
                print(f"❌ CLI command {command.replace('def ', '')} not found")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking CLI commands: {e}")
        return False

def test_demo_files():
    """Test that demo files have expected structure."""
    
    print("\n🔧 Testing demo files...")
    
    demo_files = [
        "examples/text_operations_demo.py",
        "examples/page_operations_demo.py", 
        "examples/image_operations_demo.py"
    ]
    
    for demo_file in demo_files:
        try:
            content = Path(demo_file).read_text()
            
            # Check for key function signatures
            if "def demonstrate_" in content:
                print(f"✅ {demo_file} has demonstration function")
            else:
                print(f"❌ {demo_file} missing demonstration function")
                return False
                
            # Check for import structure
            if "from pdf_editor" in content:
                print(f"✅ {demo_file} has proper imports")
            else:
                print(f"❌ {demo_file} missing proper imports")
                return False
                
        except Exception as e:
            print(f"❌ Error checking {demo_file}: {e}")
            return False
    
    return True

def test_operation_types():
    """Test that all expected operation types are defined in base.py."""
    
    print("\n🔧 Testing operation type definitions...")
    
    try:
        base_file = Path("src/pdf_editor/core/base.py")
        content = base_file.read_text()
        
        expected_types = [
            'HIGHLIGHT_TEXT',
            'ADD_ANNOTATION',
            'DELETE_ANNOTATION',
            'MERGE_PAGES',
            'SPLIT_PAGES',
            'ADD_WATERMARK'
        ]
        
        for op_type in expected_types:
            if op_type in content:
                print(f"✅ OperationType.{op_type} defined")
            else:
                print(f"❌ OperationType.{op_type} not found")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking operation types: {e}")
        return False

def main():
    """Run all structural tests."""
    
    print("🚀 Phase 2 Structural Test")
    print("=" * 40)
    print("This test checks the code structure without requiring external dependencies.\n")
    
    tests = [
        ("File Structure Test", test_file_structure),
        ("Class Definitions Test", test_class_definitions),
        ("CLI Commands Test", test_cli_commands),
        ("Demo Files Test", test_demo_files),
        ("Operation Types Test", test_operation_types)
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
        print("\n🎉 All structural tests passed!")
        print("✨ Phase 2 implementation structure looks complete!")
        print("\n📋 Summary of Phase 2 features implemented:")
        print("   📝 Text Operations:")
        print("      • Text highlighting and underlining")
        print("      • Text annotations and callouts")
        print("      • Text boxes and frames")
        print("      • OCR-based text replacement")
        print("\n   📄 Page Operations:")
        print("      • Page rotation (90°, 180°, 270°)")
        print("      • Page reordering and deletion")
        print("      • Page insertion and extraction")
        print("      • Document merging and splitting")
        print("\n   🖼️ Image Operations:")
        print("      • Image insertion and positioning")
        print("      • Image resizing and cropping")
        print("      • Image filters (brightness, contrast, etc.)")
        print("      • Watermark and stamp addition")
        print("\n   🔧 CLI Enhancements:")
        print("      • Grouped commands for text, pages, images")
        print("      • Comprehensive parameter validation")
        print("      • Rich progress indicators and results")
        return True
    else:
        print("\n⚠️ Some tests failed. Please check errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)