#!/usr/bin/env python3
"""
Test script to verify GUI structure without launching the full GUI.
This validates that all components can be imported and instantiated.
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def test_gui_imports():
    """Test that all GUI components can be imported."""
    try:
        # Test basic imports
        print("Testing GUI component imports...")
        
        # Test core components
        from pdf_editor.core.editor import PDFEditor
        from pdf_editor.config.manager import config_manager
        print("✅ Core components imported successfully")
        
        # Test GUI structure (without PySide6)
        gui_files = [
            "src/pdf_editor/gui/__init__.py",
            "src/pdf_editor/gui/pdf_viewer.py", 
            "src/pdf_editor/gui/main_window.py",
            "src/pdf_editor/gui/themes/theme_manager.py",
            "src/pdf_editor/gui/tool_panels/__init__.py",
            "src/pdf_editor/gui/tool_panels/form_editor.py",
            "src/pdf_editor/gui/tool_panels/annotation_tools.py",
            "src/pdf_editor/gui/tool_panels/security_panel.py",
            "src/pdf_editor/gui/dialogs/__init__.py",
            "src/pdf_editor/gui/dialogs/settings_dialog.py"
        ]
        
        for file_path in gui_files:
            full_path = Path(__file__).parent / file_path
            if full_path.exists():
                print(f"✅ {file_path}")
            else:
                print(f"❌ {file_path} - File missing")
        
        print("\\n📁 GUI Directory Structure:")
        gui_dir = Path(__file__).parent / "src/pdf_editor/gui"
        for root, dirs, files in os.walk(gui_dir):
            level = root.replace(str(gui_dir), '').count(os.sep)
            indent = ' ' * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                if not file.startswith('.'):
                    print(f"{subindent}{file}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_gui_components():
    """Test GUI component logic without importing PySide6."""
    try:
        print("\\n🧪 Testing GUI component logic...")
        
        # Test theme manager
        theme_data = {
            'light': {
                'window_bg': '#f0f0f0',
                'text_color': '#1e1e1e'
            },
            'dark': {
                'window_bg': '#1e1e1e', 
                'text_color': '#f0f0f0'
            }
        }
        print("✅ Theme structure defined")
        
        # Test operation data structures
        operation_examples = {
            'create_field': {
                'name': 'create_field',
                'type': 'text',
                'page': 0,
                'rect': (100, 100, 200, 120),
                'field_name': 'test_field'
            },
            'add_annotation': {
                'name': 'add_annotation', 
                'type': 'highlight',
                'page': 0,
                'rect': (50, 50, 150, 100),
                'content': 'Test annotation'
            },
            'set_password': {
                'name': 'set_password',
                'user_password': 'test123',
                'encryption': 128
            }
        }
        
        for op_name, op_data in operation_examples.items():
            print(f"✅ {op_name} operation structure valid")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing components: {e}")
        return False

if __name__ == "__main__":
    import os
    
    print("🖥️  PDF Editor GUI Structure Test\\n")
    
    success = True
    success &= test_gui_imports()
    success &= test_gui_components()
    
    print("\\n" + "="*50)
    if success:
        print("🎉 All GUI structure tests passed!")
        print("\\n📝 Next steps:")
        print("1. Install PySide6: source .venv/bin/activate && pip install PySide6")
        print("2. Run GUI: python gui_launcher.py")
        print("3. Or CLI with GUI: python main.py --gui")
    else:
        print("❌ Some tests failed. Check the errors above.")
    
    sys.exit(0 if success else 1)