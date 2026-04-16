#!/usr/bin/env python3
"""
Quick test script to verify the qwen-code-free-providers setup.
"""

import sys
from pathlib import Path

# Test imports
print("Testing imports...")
try:
    # Test bridge server imports
    sys.path.insert(0, str(Path(__file__).parent / "qwen-code-free-providers"))
    from qwen_utils import cookie_generator, fingerprint
    print("✓ qwen_utils imports work")
except ImportError as e:
    print(f"✗ qwen_utils import failed: {e}")

try:
    # Test qwen_code_tool import
    sys.path.insert(0, str(Path(__file__).parent / "backend"))
    import qwen_code_tool
    print("✓ qwen_code_tool import works")
except ImportError as e:
    print(f"✗ qwen_code_tool import failed: {e}")

try:
    # Test tools.py import
    from tools import Tools
    print("✓ tools.py import works")
except ImportError as e:
    print(f"✗ tools.py import failed: {e}")

# Check if files exist
print("\nChecking file structure...")
files_to_check = [
    "qwen-code-free-providers/bridge_server.py",
    "qwen-code-free-providers/qwen-free",
    "qwen-code-free-providers/qwen_utils/cookie_generator.py",
    "qwen-code-free-providers/qwen_utils/fingerprint.py",
    "backend/qwen_code_tool.py",
]

for file in files_to_check:
    path = Path(__file__).parent / file
    if path.exists():
        print(f"✓ {file}")
    else:
        print(f"✗ {file} (missing)")

print("\n=== Test Complete ===")
print("\nTo start using free providers:")
print("1. cd qwen-code-free-providers")
print("2. ./qwen-free setup")
print("3. ./qwen-free server")
print("4. In another terminal: qwen")
