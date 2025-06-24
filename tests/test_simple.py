#!/usr/bin/env python3
"""Simple test of TACL parser."""

import sys
from pathlib import Path

# Add tacl_python to the path
sys.path.insert(0, str(Path(__file__).parent / "tacl_python"))

from tacl.parser import TACLParser, parse_tacl_content

# Simple test
test_content = """
# Simple test
name; string: "test"
port; int: 8080
debug; bool: true
"""

try:
    result = parse_tacl_content(test_content)
    print("Basic parsing works!")
    print(f"Result: {result}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
    import traceback

    traceback.print_exc()

# Test literal type
test_literal = """
log_level; literal["debug", "info", "warn", "error"]: "info"
"""

try:
    parser = TACLParser()
    result = parse_tacl_content(test_literal)
    print("\nLiteral type parsing works!")
    print(f"Result: {result}")
except Exception as e:
    print(f"\nLiteral Error: {type(e).__name__}: {e}")
    import traceback

    traceback.print_exc()
