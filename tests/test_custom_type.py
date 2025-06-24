#!/usr/bin/env python3
"""Test custom type definitions."""

import sys
from pathlib import Path

# Add tacl_python to the path
sys.path.insert(0, str(Path(__file__).parent / "tacl_python"))

from tacl.parser import parse_tacl_content

# Test custom type
test_content = """
@type Person:
  name; string
  age; int
  email; optional[string]

# Use the custom type
john; Person:
  name; string: "John Doe"
  age; int: 30
  email; string: "john@example.com"

jane; Person:
  name; string: "Jane Smith"
  age; int: 25
  email; null: null
"""

try:
    result = parse_tacl_content(test_content)
    print("Custom type parsing works!")
    print(f"Result: {result}")
    print(f"\nJohn: {result.get('john')}")
    print(f"Jane: {result.get('jane')}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
    import traceback

    traceback.print_exc()
