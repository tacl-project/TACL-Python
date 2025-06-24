#!/usr/bin/env python3
"""Test our type checking system."""

from sys import path as sys_path

sys_path.insert(0, ".")
from tacl.parser import TACLParser
from tacl.utils import type_check


def test_type_checking():
    """Test that our type checking catches errors."""
    parser = TACLParser()

    # Test basic type checking
    try:
        type_check("hello", str, "test_string")
        print("✅ String type check passed")
    except TypeError as e:
        print(f"❌ String type check failed: {e}")

    try:
        type_check(123, str, "test_bad_string")
        print("❌ Bad string type check should have failed")
    except TypeError as e:
        print(f"✅ Bad string type check caught: {e}")

    # Test function parameter checking
    try:
        parser.parse_type("string")
        print("✅ Valid parse_type call passed")
    except TypeError as e:
        print(f"❌ Valid parse_type failed: {e}")

    try:
        parser.parse_type(123)  # Should fail - not a string
        print("❌ Bad parse_type should have failed")
    except TypeError as e:
        print(f"✅ Bad parse_type caught: {e}")


if __name__ == "__main__":
    test_type_checking()
