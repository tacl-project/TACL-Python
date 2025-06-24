#!/usr/bin/env python3
"""Test YAML-style list parsing in TACL."""

import sys

sys.path.insert(0, "tacl_python")
from tacl.api import loads
from tacl.cli import compile_to_json, compile_to_yaml


def test_yaml_list_parsing():
    """Test that YAML-style lists are parsed correctly."""
    # Test basic YAML list
    tacl_content = """
# Test YAML-style list
colors; list[string]:
  - "red"
  - "green"
  - "blue"

# Test list with different types
mixed; list[object]:
  - "string value"
  - 42
  - true
  - null

# Test nested in object
config; dict[string, object]:
  name: "test"
  ports:
    - 8080
    - 8443
  features:
    - "auth"
    - "logging"

# Test list at root level with union type
log_config; dict[string, union[string, list[string]]]:
  level: "info"
  format: "json"
  outputs:
    - "stdout"
    - "file"
"""

    print("Testing YAML-style list parsing...")

    # Parse the content
    result = loads(tacl_content)

    # Verify basic list
    assert result["colors"] == ["red", "green", "blue"], (
        f"Expected ['red', 'green', 'blue'], got {result['colors']}"
    )
    print("✓ Basic string list parsed correctly")

    # Verify mixed type list
    assert result["mixed"] == ["string value", 42, True, None], (
        f"Expected mixed list, got {result['mixed']}"
    )
    print("✓ Mixed type list parsed correctly")

    # Verify nested lists in object
    assert result["config"]["ports"] == [8080, 8443], (
        f"Expected [8080, 8443], got {result['config']['ports']}"
    )
    assert result["config"]["features"] == ["auth", "logging"], (
        f"Expected ['auth', 'logging'], got {result['config']['features']}"
    )
    print("✓ Nested lists in object parsed correctly")

    # Verify union type with list
    assert result["log_config"]["outputs"] == ["stdout", "file"], (
        f"Expected ['stdout', 'file'], got {result['log_config']['outputs']}"
    )
    print("✓ List with union type parsed correctly")

    # Test compilation to different formats
    print("\nTesting export to different formats...")

    # Compile to YAML
    yaml_output = compile_to_yaml(tacl_content)
    print("YAML output:")
    print(yaml_output)

    # Compile to JSON
    json_output = compile_to_json(tacl_content)
    print("\nJSON output:")
    print(json_output)

    print("\n✅ All YAML-style list tests passed!")


def test_complex_yaml_lists():
    """Test more complex YAML list scenarios."""
    tacl_content = """
# Test list with references
servers; list[string]:
  - "server1"
  - "server2"

primary_server; string: &servers[0]

# Test nested lists
matrix; list[list[int]]:
  -
    - 1
    - 2
    - 3
  -
    - 4
    - 5
    - 6

# Test list with multiline strings
messages; list[string]:
  - "Simple message"
  - |
    This is a multiline
    message that preserves
    line breaks
  - "Another simple message"
"""

    print("\n\nTesting complex YAML-style lists...")

    result = loads(tacl_content)

    # Verify reference to list item
    assert result["primary_server"] == "server1", (
        f"Expected 'server1', got {result['primary_server']}"
    )
    print("✓ Reference to list item resolved correctly")

    # Verify nested lists
    expected_matrix = [[1, 2, 3], [4, 5, 6]]
    assert result["matrix"] == expected_matrix, (
        f"Expected {expected_matrix}, got {result['matrix']}"
    )
    print("✓ Nested lists parsed correctly")

    # Verify multiline strings in lists
    assert len(result["messages"]) == 3
    assert "This is a multiline" in result["messages"][1]
    assert "line breaks" in result["messages"][1]
    print("✓ Multiline strings in lists parsed correctly")

    print("\n✅ All complex YAML-style list tests passed!")


if __name__ == "__main__":
    test_yaml_list_parsing()
    test_complex_yaml_lists()
