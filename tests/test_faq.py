#!/usr/bin/env python3
"""Test the TACL parser with the FAQ example."""

import sys
from pathlib import Path

# Add src to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tacl.api import load

try:
    # Load the FAQ example
    data = load("faq.tacl")
    print("Successfully parsed faq.tacl!")
    print(f"Number of fields: {len(data)}")

    # Print some example data
    if "motivation" in data:
        print(f"\nMotivation question: {data['motivation']['q']}")

    if "categories" in data:
        print(f"\nNumber of categories: {len(data['categories'])}")

except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
    import traceback

    traceback.print_exc()
