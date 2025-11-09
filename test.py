"""
Test script to verify all dependencies and modules are working
Run this before starting the main app to catch any issues early
"""

import sys

print("=" * 60)
print("🧪 Testing Credit Card Parser Setup")
print("=" * 60)
print()

# Test 1: Python version
print("1️⃣ Checking Python version...")
if sys.version_info >= (3, 10):
    print(f"   ✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
else:
    print(f"   ❌ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    print("   ⚠️  Python 3.10+ required!")
    sys.exit(1)

# Test 2: Required packages
print("\n2️⃣ Checking required packages...")
required_packages = {
    'streamlit': 'Streamlit',
    'pdfplumber': 'PDFPlumber',
    'pandas': 'Pandas',
    'dateutil': 'python-dateutil',
    'PIL': 'Pillow'
}

missing_packages = []
for package, name in required_packages.items():
    try:
        __import__(package)
        print(f"   ✅ {name}")
    except ImportError:
        print(f"   ❌ {name} - NOT INSTALLED")
        missing_packages.append(name)

if missing_packages:
    print(f"\n   ⚠️  Missing packages: {', '.join(missing_packages)}")
    print("   Run: pip install -r requirements.txt")
    sys.exit(1)

# Test 3: Local modules
print("\n3️⃣ Checking local modules...")
local_modules = ['config', 'utils', 'parser', 'extractors', 'validators']

missing_modules = []
for module in local_modules:
    try:
        __import__(module)
        print(f"   ✅ {module}.py")
    except ImportError as e:
        print(f"   ❌ {module}.py - NOT FOUND")
        missing_modules.append(module)
    except Exception as e:
        print(f"   ⚠️  {module}.py - ERROR: {str(e)}")
        missing_modules.append(module)

if missing_modules:
    print(f"\n   ⚠️  Missing modules: {', '.join(missing_modules)}")
    print("   Make sure all .py files are created in the project folder")
    sys.exit(1)

# Test 4: Import main components
print("\n4️⃣ Testing main components...")
try:
    from parser import PDFParser
    print("   ✅ PDFParser class")
except Exception as e:
    print(f"   ❌ PDFParser - {str(e)}")
    sys.exit(1)

try:
    from extractors import FieldExtractor
    print("   ✅ FieldExtractor class")
except Exception as e:
    print(f"   ❌ FieldExtractor - {str(e)}")
    sys.exit(1)

try:
    from cc_validators import validate_all_fields
    print("   ✅ Validators")
except Exception as e:
    print(f"   ❌ Validators - {str(e)}")
    sys.exit(1)

try:
    from config import ISSUERS, FIELD_NAMES
    print(f"   ✅ Configuration ({len(ISSUERS)} issuers loaded)")
    
    # Verify IDFC First Bank is configured
    if 'IDFC' in ISSUERS:
        print(f"   ✅ IDFC First Bank configuration found")
    else:
        print(f"   ⚠️  IDFC First Bank not found in configuration")
except Exception as e:
    print(f"   ❌ Config - {str(e)}")
    sys.exit(1)

# Test 5: Utility functions
print("\n5️⃣ Testing utility functions...")
try:
    from utils import normalize_text, parse_date, extract_amount, extract_last4_digits
    
    # Test normalize_text
    test_text = "  Hello   World  "
    result = normalize_text(test_text)
    assert result == "Hello World", "normalize_text failed"
    print("   ✅ normalize_text()")
    
    # Test parse_date
    test_date = "01/12/2024"
    result = parse_date(test_date)
    assert result is not None, "parse_date failed"
    print("   ✅ parse_date()")
    
    # Test extract_amount
    test_amount = "₹1,234.56"
    result = extract_amount(test_amount)
    assert result == 1234.56, f"extract_amount failed: got {result}"
    print("   ✅ extract_amount()")
    
    # Test extract_last4_digits
    test_card = "XXXX XXXX XXXX 1234"
    result = extract_last4_digits(test_card)
    assert result == "1234", "extract_last4_digits failed"
    print("   ✅ extract_last4_digits()")
    
except AssertionError as e:
    print(f"   ❌ Utility test failed: {str(e)}")
    sys.exit(1)
except Exception as e:
    print(f"   ❌ Utility functions error: {str(e)}")
    sys.exit(1)

# Test 6: Check project structure
print("\n6️⃣ Checking project structure...")
import os

required_files = [
    'app.py',
    'parser.py',
    'extractors.py',
    'config.py',
    'utils.py',
    'validators.py',
    'requirements.txt',
    'README.md'
]

missing_files = []
for file in required_files:
    if os.path.exists(file):
        print(f"   ✅ {file}")
    else:
        print(f"   ❌ {file} - NOT FOUND")
        missing_files.append(file)

if missing_files:
    print(f"\n   ⚠️  Missing files: {', '.join(missing_files)}")
    print("   Create these files in your project folder")
    sys.exit(1)

# Test 7: Sample folder
print("\n7️⃣ Checking sample statements folder...")
if os.path.exists('sample_statements'):
    pdf_files = [f for f in os.listdir('sample_statements') if f.endswith('.pdf')]
    if pdf_files:
        print(f"    sample_statements/ folder exists ({len(pdf_files)} PDFs found)")
    else:
        print(f"    sample_statements/ folder exists but no PDFs found")
        print("   Add test PDFs to this folder for testing")
else:
    print("    sample_statements/ folder not found")
    print("   Create this folder and add test PDFs")

# All tests passed!
print("\n" + "=" * 60)
print(" All tests passed! Your setup is ready.")
print("=" * 60)
print("\n🚀 Next steps:")
print("   1. Add test PDFs to sample_statements/ folder")
print("   2. Run: streamlit run app.py")
print("   3. Open browser to http://localhost:8501")
print("   4. Upload a PDF and test extraction")
print("\n💡 Tip: Keep this terminal open while using the app")
print("=" * 60)