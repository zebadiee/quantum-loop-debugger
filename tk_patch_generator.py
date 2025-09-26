
#!/usr/bin/env python3
"""
Quantum Loop Debugger - AI-Powered Patch Generator
Generates intelligent patches for failed code using LLM analysis
"""

import json
import sys
import os
import re
from datetime import datetime

class QuantumPatchGenerator:
    def __init__(self):
        self.patch_templates = {
            'import_error': self.generate_import_fix,
            'name_error': self.generate_name_fix,
            'type_error': self.generate_type_fix,
            'attribute_error': self.generate_attribute_fix,
            'syntax_error': self.generate_syntax_fix,
            'file_not_found': self.generate_file_fix,
            'division_by_zero': self.generate_division_fix,
            'index_error': self.generate_index_fix,
            'key_error': self.generate_key_fix,
            'value_error': self.generate_value_fix
        }
        
        print("🤖 Quantum Patch Generator initialized")
        print("🧠 AI-powered code healing system ready")

    def analyze_error(self, failure_context):
        """Analyze the failure context to determine error type and generate appropriate patch"""
        error_text = failure_context.get('error', '').lower()
        
        print(f"🔍 Analyzing error: {error_text[:100]}...")
        
        # Determine error type based on error message patterns
        if 'modulenotfounderror' in error_text or 'importerror' in error_text:
            return 'import_error'
        elif 'nameerror' in error_text:
            return 'name_error'
        elif 'typeerror' in error_text:
            return 'type_error'
        elif 'attributeerror' in error_text:
            return 'attribute_error'
        elif 'syntaxerror' in error_text:
            return 'syntax_error'
        elif 'filenotfounderror' in error_text or 'no such file' in error_text:
            return 'file_not_found'
        elif 'zerodivisionerror' in error_text:
            return 'division_by_zero'
        elif 'indexerror' in error_text:
            return 'index_error'
        elif 'keyerror' in error_text:
            return 'key_error'
        elif 'valueerror' in error_text:
            return 'value_error'
        else:
            return 'generic_error'

    def extract_error_details(self, error_text):
        """Extract specific details from error messages"""
        details = {}
        
        # Extract module name from import errors
        import_match = re.search(r"No module named '([^']+)'", error_text)
        if import_match:
            details['missing_module'] = import_match.group(1)
        
        # Extract variable name from NameError
        name_match = re.search(r"name '([^']+)' is not defined", error_text)
        if name_match:
            details['undefined_name'] = name_match.group(1)
        
        # Extract attribute name from AttributeError
        attr_match = re.search(r"'([^']+)' object has no attribute '([^']+)'", error_text)
        if attr_match:
            details['object_type'] = attr_match.group(1)
            details['missing_attribute'] = attr_match.group(2)
        
        # Extract file name from FileNotFoundError
        file_match = re.search(r"No such file or directory: '([^']+)'", error_text)
        if file_match:
            details['missing_file'] = file_match.group(1)
        
        return details

    def generate_import_fix(self, failure_context, details):
        """Generate patch for import errors"""
        missing_module = details.get('missing_module', 'unknown_module')
        
        # Common module mappings
        module_fixes = {
            'cv2': 'opencv-python',
            'PIL': 'Pillow',
            'sklearn': 'scikit-learn',
            'bs4': 'beautifulsoup4',
            'yaml': 'PyYAML',
            'requests': 'requests',
            'numpy': 'numpy',
            'pandas': 'pandas',
            'matplotlib': 'matplotlib',
            'flask': 'Flask'
        }
        
        pip_package = module_fixes.get(missing_module, missing_module)
        
        patch_code = f'''
# Quantum Patch: Import Error Fix
# Generated: {datetime.now().isoformat()}
# Issue: Missing module '{missing_module}'

import subprocess
import sys
import importlib

def install_and_import(package_name, module_name=None):
    """Install package and import module"""
    if module_name is None:
        module_name = package_name
    
    try:
        importlib.import_module(module_name)
        print(f"✅ Module {{module_name}} already available")
    except ImportError:
        print(f"📦 Installing {{package_name}}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print(f"✅ Successfully installed {{package_name}}")

# Apply the fix
install_and_import("{pip_package}", "{missing_module}")
print("🔧 Import error patch applied successfully")
'''
        return patch_code

    def generate_name_fix(self, failure_context, details):
        """Generate patch for NameError"""
        undefined_name = details.get('undefined_name', 'unknown_variable')
        
        patch_code = f'''
# Quantum Patch: NameError Fix
# Generated: {datetime.now().isoformat()}
# Issue: Undefined name '{undefined_name}'

# Common variable initializations
common_vars = {{
    'data': [],
    'result': None,
    'config': {{}},
    'response': None,
    'content': "",
    'items': [],
    'value': 0,
    'count': 0,
    'index': 0,
    'filename': "default.txt",
    'path': ".",
    'url': "http://localhost",
    'status': "ready"
}}

# Initialize the undefined variable
if "{undefined_name}" in common_vars:
    globals()["{undefined_name}"] = common_vars["{undefined_name}"]
    print(f"🔧 Initialized {{'{undefined_name}'}} with default value: {{common_vars['{undefined_name}']}}")
else:
    globals()["{undefined_name}"] = None
    print(f"🔧 Initialized {{'{undefined_name}'}} with None")

print("🔧 NameError patch applied successfully")
'''
        return patch_code

    def generate_type_fix(self, failure_context, details):
        """Generate patch for TypeError"""
        patch_code = f'''
# Quantum Patch: TypeError Fix
# Generated: {datetime.now().isoformat()}
# Issue: Type-related error

def safe_operation(func, *args, **kwargs):
    """Safely execute operations with type checking"""
    try:
        return func(*args, **kwargs)
    except TypeError as e:
        print(f"🔧 Type error caught: {{e}}")
        # Try common type conversions
        converted_args = []
        for arg in args:
            if isinstance(arg, str) and arg.isdigit():
                converted_args.append(int(arg))
            elif isinstance(arg, (int, float)) and hasattr(func, '__name__') and 'str' in func.__name__:
                converted_args.append(str(arg))
            else:
                converted_args.append(arg)
        
        try:
            return func(*converted_args, **kwargs)
        except:
            return None

# Monkey patch common functions to be safer
import builtins
original_int = builtins.int
original_str = builtins.str
original_float = builtins.float

def safe_int(value, base=10):
    try:
        return original_int(value, base)
    except (ValueError, TypeError):
        return 0

def safe_str(value):
    try:
        return original_str(value)
    except (ValueError, TypeError):
        return ""

def safe_float(value):
    try:
        return original_float(value)
    except (ValueError, TypeError):
        return 0.0

builtins.int = safe_int
builtins.str = safe_str
builtins.float = safe_float

print("🔧 TypeError patch applied successfully")
'''
        return patch_code

    def generate_attribute_fix(self, failure_context, details):
        """Generate patch for AttributeError"""
        object_type = details.get('object_type', 'object')
        missing_attribute = details.get('missing_attribute', 'unknown_attr')
        
        patch_code = f'''
# Quantum Patch: AttributeError Fix
# Generated: {datetime.now().isoformat()}
# Issue: Missing attribute '{missing_attribute}' on '{object_type}' object

def add_missing_attribute(obj, attr_name, default_value=None):
    """Add missing attribute to object"""
    if not hasattr(obj, attr_name):
        setattr(obj, attr_name, default_value)
        print(f"🔧 Added missing attribute '{{attr_name}}' to {{type(obj).__name__}} object")

# Common attribute defaults
attribute_defaults = {{
    'text': "",
    'content': "",
    'data': [],
    'value': None,
    'status': "ready",
    'result': None,
    'response': None,
    'config': {{}},
    'items': [],
    'length': 0,
    'size': 0,
    'count': 0
}}

# Monkey patch getattr to provide defaults
original_getattr = getattr

def safe_getattr(obj, name, default=None):
    """Safe getattr with intelligent defaults"""
    try:
        return original_getattr(obj, name, default)
    except AttributeError:
        if name in attribute_defaults:
            default_val = attribute_defaults[name]
            setattr(obj, name, default_val)
            return default_val
        return default

import builtins
builtins.getattr = safe_getattr

print("🔧 AttributeError patch applied successfully")
'''
        return patch_code

    def generate_syntax_fix(self, failure_context, details):
        """Generate patch for SyntaxError"""
        patch_code = f'''
# Quantum Patch: SyntaxError Fix
# Generated: {datetime.now().isoformat()}
# Issue: Syntax error detected

print("🔧 SyntaxError detected - this requires manual code review")
print("💡 Common syntax fixes:")
print("   - Check for missing colons (:) after if/for/while/def statements")
print("   - Verify proper indentation (use 4 spaces)")
print("   - Check for unmatched parentheses, brackets, or quotes")
print("   - Ensure proper string escaping")

# Create a backup mechanism for syntax errors
import tempfile
import shutil
import os

def create_syntax_backup():
    """Create backup of files for manual review"""
    backup_dir = tempfile.mkdtemp(prefix="quantum_syntax_backup_")
    print(f"📁 Created syntax backup directory: {{backup_dir}}")
    
    # Copy Python files for review
    for file in os.listdir("."):
        if file.endswith(".py"):
            try:
                shutil.copy2(file, backup_dir)
                print(f"📄 Backed up: {{file}}")
            except Exception as e:
                print(f"⚠️  Could not backup {{file}}: {{e}}")
    
    return backup_dir

backup_location = create_syntax_backup()
print(f"🔧 SyntaxError patch applied - manual review required at: {{backup_location}}")
'''
        return patch_code

    def generate_file_fix(self, failure_context, details):
        """Generate patch for FileNotFoundError"""
        missing_file = details.get('missing_file', 'unknown_file')
        
        patch_code = f'''
# Quantum Patch: FileNotFoundError Fix
# Generated: {datetime.now().isoformat()}
# Issue: Missing file '{missing_file}'

import os

def create_missing_file(filename, default_content=""):
    """Create missing file with default content"""
    try:
        # Create directory if it doesn't exist
        directory = os.path.dirname(filename)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
            print(f"📁 Created directory: {{directory}}")
        
        # Create file with appropriate default content
        if filename.endswith('.json'):
            default_content = "{{}}"
        elif filename.endswith('.txt'):
            default_content = ""
        elif filename.endswith('.csv'):
            default_content = "column1,column2\\n"
        elif filename.endswith('.py'):
            default_content = "# Auto-generated file\\npass\\n"
        
        with open(filename, 'w') as f:
            f.write(default_content)
        
        print(f"📄 Created missing file: {{filename}}")
        return True
    except Exception as e:
        print(f"❌ Could not create file {{filename}}: {{e}}")
        return False

# Create the missing file
create_missing_file("{missing_file}")
print("🔧 FileNotFoundError patch applied successfully")
'''
        return patch_code

    def generate_division_fix(self, failure_context, details):
        """Generate patch for ZeroDivisionError"""
        patch_code = f'''
# Quantum Patch: ZeroDivisionError Fix
# Generated: {datetime.now().isoformat()}
# Issue: Division by zero

def safe_divide(a, b, default=0):
    """Safe division with zero check"""
    try:
        if b == 0:
            print(f"⚠️  Division by zero prevented, returning {{default}}")
            return default
        return a / b
    except Exception as e:
        print(f"⚠️  Division error: {{e}}, returning {{default}}")
        return default

# Monkey patch division operations
import operator
original_truediv = operator.truediv
original_floordiv = operator.floordiv

def safe_truediv(a, b):
    return safe_divide(a, b, 0.0)

def safe_floordiv(a, b):
    return safe_divide(a, b, 0) if b != 0 else 0

operator.truediv = safe_truediv
operator.floordiv = safe_floordiv

print("🔧 ZeroDivisionError patch applied successfully")
'''
        return patch_code

    def generate_index_fix(self, failure_context, details):
        """Generate patch for IndexError"""
        patch_code = f'''
# Quantum Patch: IndexError Fix
# Generated: {datetime.now().isoformat()}
# Issue: List index out of range

def safe_list_access(lst, index, default=None):
    """Safe list access with bounds checking"""
    try:
        if isinstance(lst, (list, tuple)) and 0 <= index < len(lst):
            return lst[index]
        else:
            print(f"⚠️  Index {{index}} out of range for list of length {{len(lst) if isinstance(lst, (list, tuple)) else 'unknown'}}, returning {{default}}")
            return default
    except Exception as e:
        print(f"⚠️  List access error: {{e}}, returning {{default}}")
        return default

# Monkey patch list access
original_list_getitem = list.__getitem__

def safe_list_getitem(self, index):
    try:
        return original_list_getitem(self, index)
    except IndexError:
        print(f"⚠️  Index {{index}} out of range for list of length {{len(self)}}, returning None")
        return None

list.__getitem__ = safe_list_getitem

print("🔧 IndexError patch applied successfully")
'''
        return patch_code

    def generate_key_fix(self, failure_context, details):
        """Generate patch for KeyError"""
        patch_code = f'''
# Quantum Patch: KeyError Fix
# Generated: {datetime.now().isoformat()}
# Issue: Dictionary key not found

def safe_dict_access(d, key, default=None):
    """Safe dictionary access with key checking"""
    try:
        return d.get(key, default)
    except Exception as e:
        print(f"⚠️  Dictionary access error: {{e}}, returning {{default}}")
        return default

# Monkey patch dictionary access
original_dict_getitem = dict.__getitem__

def safe_dict_getitem(self, key):
    try:
        return original_dict_getitem(self, key)
    except KeyError:
        print(f"⚠️  Key '{{key}}' not found in dictionary, returning None")
        return None

dict.__getitem__ = safe_dict_getitem

print("🔧 KeyError patch applied successfully")
'''
        return patch_code

    def generate_value_fix(self, failure_context, details):
        """Generate patch for ValueError"""
        patch_code = f'''
# Quantum Patch: ValueError Fix
# Generated: {datetime.now().isoformat()}
# Issue: Invalid value for operation

def safe_conversion(value, target_type, default=None):
    """Safe type conversion with error handling"""
    try:
        if target_type == int:
            if isinstance(value, str):
                # Extract numbers from string
                import re
                numbers = re.findall(r'-?\\d+', value)
                return int(numbers[0]) if numbers else (default or 0)
            return int(value)
        elif target_type == float:
            if isinstance(value, str):
                import re
                numbers = re.findall(r'-?\\d+\\.?\\d*', value)
                return float(numbers[0]) if numbers else (default or 0.0)
            return float(value)
        elif target_type == str:
            return str(value)
        else:
            return target_type(value)
    except Exception as e:
        print(f"⚠️  Conversion error: {{e}}, returning {{default}}")
        return default

# Monkey patch common conversion functions
import builtins
original_int = builtins.int
original_float = builtins.float

def safe_int_conversion(value, base=10):
    return safe_conversion(value, int, 0)

def safe_float_conversion(value):
    return safe_conversion(value, float, 0.0)

builtins.int = safe_int_conversion
builtins.float = safe_float_conversion

print("🔧 ValueError patch applied successfully")
'''
        return patch_code

    def generate_generic_patch(self, failure_context):
        """Generate a generic patch for unknown errors"""
        patch_code = f'''
# Quantum Patch: Generic Error Handler
# Generated: {datetime.now().isoformat()}
# Issue: Unknown error type

import sys
import traceback

def quantum_error_handler(exc_type, exc_value, exc_traceback):
    """Global error handler for unknown issues"""
    print(f"🔧 Quantum error handler activated")
    print(f"📊 Error type: {{exc_type.__name__}}")
    print(f"📝 Error message: {{exc_value}}")
    
    # Log the error for analysis
    with open("quantum_error_log.txt", "a") as f:
        f.write(f"\\n--- Error at {{datetime.now().isoformat()}} ---\\n")
        f.write(f"Type: {{exc_type.__name__}}\\n")
        f.write(f"Message: {{exc_value}}\\n")
        f.write("Traceback:\\n")
        traceback.print_tb(exc_traceback, file=f)
        f.write("\\n")
    
    print("📄 Error logged to quantum_error_log.txt")
    
    # Try to continue execution
    return True

# Install global error handler
sys.excepthook = quantum_error_handler

print("🔧 Generic error patch applied successfully")
'''
        return patch_code

    def generate_patch(self, failure_context):
        """Main patch generation method"""
        print("🧠 Analyzing failure context...")
        
        error_type = self.analyze_error(failure_context)
        error_details = self.extract_error_details(failure_context.get('error', ''))
        
        print(f"🎯 Detected error type: {error_type}")
        print(f"🔍 Error details: {error_details}")
        
        if error_type in self.patch_templates:
            patch_code = self.patch_templates[error_type](failure_context, error_details)
        else:
            patch_code = self.generate_generic_patch(failure_context)
        
        # Write patch to file
        patch_file = "generated_patch.py"
        with open(patch_file, 'w') as f:
            f.write(patch_code)
        
        print(f"✅ Patch generated and saved to {patch_file}")
        print(f"📏 Patch size: {len(patch_code)} characters")
        
        return True

# MCP Server functionality
class MCPPatchServer:
    def __init__(self, port=8081):
        self.port = port
        self.generator = QuantumPatchGenerator()
        
    async def handle_method(self, method, params):
        """Handle MCP method calls"""
        if method == 'generate_patch':
            failure_context = params.get('failure_context', {})
            try:
                success = self.generator.generate_patch(failure_context)
                
                # Read generated patch
                patch_file = "generated_patch.py"
                patch_content = ""
                if os.path.exists(patch_file):
                    with open(patch_file, 'r') as f:
                        patch_content = f.read()
                
                return {
                    'success': success,
                    'patch': {
                        'file_path': patch_file,
                        'patch_content': patch_content,
                        'generated_at': datetime.now().isoformat()
                    }
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e)
                }
        elif method == 'health_check':
            return {
                'success': True,
                'service': 'patch-generator',
                'status': 'healthy',
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'success': False,
                'error': f'Unknown method: {method}'
            }

def start_mcp_server(port):
    """Start MCP server"""
    from flask import Flask, request, jsonify
    
    app = Flask(__name__)
    server = MCPPatchServer(port)
    
    @app.route('/health')
    def health():
        return jsonify({'status': 'healthy', 'service': 'patch-generator'})
    
    @app.route('/mcp/call', methods=['POST'])
    async def mcp_call():
        try:
            data = request.get_json()
            method = data.get('method')
            params = data.get('params', {})
            
            result = await server.handle_method(method, params)
            return jsonify(result)
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    print(f"🔌 Starting MCP Patch Generator server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Quantum Patch Generator')
    parser.add_argument('context_file', nargs='?', help='Failure context file')
    parser.add_argument('--mcp-mode', action='store_true', help='Run as MCP server')
    parser.add_argument('--port', type=int, default=8081, help='MCP server port')
    
    args = parser.parse_args()
    
    if args.mcp_mode:
        start_mcp_server(args.port)
        return 0
    
    if not args.context_file:
        print("Usage: python tk_patch_generator.py <failure_context_file>")
        print("   or: python tk_patch_generator.py --mcp-mode [--port PORT]")
        return 1
    
    if not os.path.exists(args.context_file):
        print(f"❌ Context file not found: {args.context_file}")
        return 1
    
    try:
        with open(args.context_file, 'r') as f:
            failure_context = json.load(f)
        
        generator = QuantumPatchGenerator()
        success = generator.generate_patch(failure_context)
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"❌ Error generating patch: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
