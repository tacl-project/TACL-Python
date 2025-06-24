#!/usr/bin/env python3
"""Test the exact log configuration example from the user."""

import sys

sys.path.insert(0, "../src")
from tacl.api import loads
from tacl.cli import compile_to_yaml


def test_log_config():
    """Test the exact log configuration from the screenshot."""
    tacl_content = """
# Log configuration
log_config; dict[string, union[string,list[string]]]:
  level: "info"
  format: "json"
  outputs:
    - "stdout"
    - "file"
"""

    print("Testing log configuration...")

    # Parse the content
    result = loads(tacl_content)

    # Verify the structure
    assert "log_config" in result
    assert result["log_config"]["level"] == "info"
    assert result["log_config"]["format"] == "json"
    assert result["log_config"]["outputs"] == ["stdout", "file"]

    print("✓ Log configuration parsed correctly")
    print(f"  level: {result['log_config']['level']}")
    print(f"  format: {result['log_config']['format']}")
    print(f"  outputs: {result['log_config']['outputs']}")

    # Show YAML output
    yaml_output = compile_to_yaml(tacl_content)
    print("\nYAML output:")
    print(yaml_output)

    print("\n✅ Log configuration test passed!")


if __name__ == "__main__":
    test_log_config()
