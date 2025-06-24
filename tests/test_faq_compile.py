#!/usr/bin/env python3
"""Test compiling faq.tacl to JSON, YAML, and TOML formats."""

import sys
from pathlib import Path

# Add src to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tacl.cli import compile_to_json, compile_to_toml, compile_to_yaml


def test_compile_faq():
    """Test compiling faq.tacl to all supported formats."""
    # Read the faq.tacl file
    try:
        with open("faq.tacl") as f:
            tacl_content = f.read()
        print("✓ Successfully read faq.tacl")
    except Exception as e:
        print(f"❌ Failed to read faq.tacl: {e}")
        return False

    # Test YAML compilation
    print("\n=== Testing YAML Compilation ===")
    try:
        yaml_output = compile_to_yaml(tacl_content)
        print("✓ Successfully compiled to YAML")
        print(f"YAML size: {len(yaml_output)} bytes")

        # Save to file
        with open("OUTPUTS/faq.yaml", "w") as f:
            f.write(yaml_output)
        print("✓ Saved to OUTPUTS/faq.yaml")

        # Show a sample
        print("\nFirst 500 chars of YAML:")
        print(yaml_output[:500] + "..." if len(yaml_output) > 500 else yaml_output)

    except Exception as e:
        print(f"❌ YAML compilation failed: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Test JSON compilation
    print("\n=== Testing JSON Compilation ===")
    try:
        json_output = compile_to_json(tacl_content)
        print("✓ Successfully compiled to JSON")
        print(f"JSON size: {len(json_output)} bytes")

        # Save to file
        with open("OUTPUTS/faq.json", "w") as f:
            f.write(json_output)
        print("✓ Saved to OUTPUTS/faq.json")

        # Show a sample
        print("\nFirst 500 chars of JSON:")
        print(json_output[:500] + "..." if len(json_output) > 500 else json_output)

    except Exception as e:
        print(f"❌ JSON compilation failed: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()

    # Test TOML compilation
    print("\n=== Testing TOML Compilation ===")
    try:
        toml_output = compile_to_toml(tacl_content)
        print("✓ Successfully compiled to TOML")
        print(f"TOML size: {len(toml_output)} bytes")

        # Save to file
        with open("OUTPUTS/faq.toml", "w") as f:
            f.write(toml_output)
        print("✓ Saved to OUTPUTS/faq.toml")

        # Show a sample
        print("\nFirst 500 chars of TOML:")
        print(toml_output[:500] + "..." if len(toml_output) > 500 else toml_output)

    except Exception as e:
        print(f"❌ TOML compilation failed: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()

    return True


if __name__ == "__main__":
    print("Testing FAQ TACL Compilation")
    print("=" * 50)

    success = test_compile_faq()

    if success:
        print("\n✅ Compilation test completed!")
    else:
        print("\n❌ Compilation test failed!")

    sys.exit(0 if success else 1)
