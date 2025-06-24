#!/usr/bin/env python3
"""Test basic imports."""

import sys
from pathlib import Path

print(f"Python version: {sys.version}")
print(f"Current directory: {Path.cwd()}")

# Add tacl_python to the path
tacl_path = Path(__file__).parent / "tacl_python"
print(f"Adding to path: {tacl_path}")
sys.path.insert(0, str(tacl_path))

try:
    print("\nTrying to import tacl.api.parser...")
    from tacl.parser import parse_tacl_content

    print("✓ Successfully imported tacl_parser")

    print("\nTrying to import tacl.api.cli...")

    print("✓ Successfully imported tacl_cli")

    print("\nTesting basic parsing...")
    test_content = 'name; string: "test"'
    result = parse_tacl_content(test_content)
    print(f"✓ Basic parsing works: {result}")

except Exception as e:
    print(f"❌ Import failed: {type(e).__name__}: {e}")
    import traceback

    traceback.print_exc()
