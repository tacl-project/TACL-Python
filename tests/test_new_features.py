#!/usr/bin/env python3
"""Comprehensive tests for new TACL features."""

import sys
from pathlib import Path

# Add tacl_python to the path if running directly
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))

from tacl.parser import ValidationError, parse_tacl_content


def test_literal_types():
    """Test literal type support."""
    print("\n=== Testing Literal Types ===")

    # String literals
    content = """
log_level; literal["debug", "info", "warn", "error"]: "info"
environment; literal["dev", "staging", "prod"]: "prod"
"""
    result = parse_tacl_content(content)
    assert result["log_level"] == "info"
    assert result["environment"] == "prod"
    print("✓ String literals work")

    # Numeric literals
    content = """
http_port; literal[80, 443, 8080, 8443]: 8080
max_retries; literal[0, 1, 3, 5, 10]: 3
threshold; literal[0.5, 0.75, 0.9, 0.95]: 0.75
"""
    result = parse_tacl_content(content)
    assert result["http_port"] == 8080
    assert result["max_retries"] == 3
    assert result["threshold"] == 0.75
    print("✓ Numeric literals work")

    # Test invalid literal value
    try:
        content = 'status; literal["active", "inactive"]: "unknown"'
        parse_tacl_content(content)
        assert False, "Should have failed with invalid literal"
    except ValidationError as e:
        assert "not in allowed values" in str(e)
        print("✓ Invalid literal values are caught")


def test_union_types():
    """Test union type support."""
    print("\n=== Testing Union Types ===")

    content = """
# Union of different types
config_value; union[string, int]: "debug"
port_or_name; union[string, int]: 8080
optional_flag; union[bool, null]: null
"""
    result = parse_tacl_content(content)
    assert result["config_value"] == "debug"
    assert result["port_or_name"] == 8080
    assert result["optional_flag"] is None
    print("✓ Union types work")

    # Test invalid union value
    try:
        content = "value; union[string, int]: 3.14"
        parse_tacl_content(content)
        assert False, "Should have failed with invalid union type"
    except ValidationError as e:
        assert "does not match any union type" in str(e)
        print("✓ Invalid union values are caught")


def test_custom_types():
    """Test @type custom type definitions."""
    print("\n=== Testing Custom Types ===")

    content = """
@type Person:
  name; string
  age; int
  email; optional[string]

@type Team:
  name; string
  lead; Person
  members; list[Person]

# Use custom types
alice; Person:
  name; string: "Alice Smith"
  age; int: 30
  email; string: "alice@example.com"

bob; Person:
  name; string: "Bob Jones"  
  age; int: 25
  email; null: null

engineering; Team:
  name; string: "Engineering"
  lead; Person: &alice
  members; list[Person]: [&alice, &bob]
"""
    result = parse_tacl_content(content)
    assert result["alice"]["name"] == "Alice Smith"
    assert result["alice"]["age"] == 30
    assert result["bob"]["email"] is None
    assert result["engineering"]["lead"]["name"] == "Alice Smith"
    assert len(result["engineering"]["members"]) == 2
    print("✓ Custom types with references work")

    # Test missing required field
    try:
        content = """
@type User:
  username; string
  password; string

invalid_user; User:
  username; string: "test"
"""
        parse_tacl_content(content)
        assert False, "Should have failed with missing field"
    except ValidationError as e:
        assert "missing required field" in str(e)
        print("✓ Missing required fields are caught")

    # Test extra field
    try:
        content = """
@type Point:
  x; int
  y; int

invalid_point; Point:
  x; int: 10
  y; int: 20
  z; int: 30
"""
        parse_tacl_content(content)
        assert False, "Should have failed with extra field"
    except ValidationError as e:
        assert "unexpected field" in str(e)
        print("✓ Extra fields are caught")


def test_object_syntax():
    """Test object syntax with indented fields."""
    print("\n=== Testing Object Syntax ===")

    content = """
# Object with indented fields
server; dict[string, object]:
  host; string: "localhost"
  port; int: 8080
  ssl; bool: true
  
# Nested objects
config; dict[string, dict[string, object]]:
  database; dict[string, object]:
    host; string: "db.example.com"
    port; int: 5432
    name; string: "myapp"
  cache; dict[string, object]:
    host; string: "cache.example.com"
    port; int: 6379
"""
    result = parse_tacl_content(content)
    assert result["server"]["host"] == "localhost"
    assert result["server"]["port"] == 8080
    assert result["config"]["database"]["name"] == "myapp"
    assert result["config"]["cache"]["port"] == 6379
    print("✓ Object syntax works")


def test_references_with_types():
    """Test reference system with typed objects."""
    print("\n=== Testing References with Types ===")

    content = """
@type Service:
  name; string
  port; int
  enabled; bool

# Define services
api_service; Service:
  name; string: "api"
  port; int: 8080
  enabled; bool: true

db_service; Service:
  name; string: "database"
  port; int: 5432
  enabled; bool: true

# Reference service fields
api_port; int: &api_service.port
db_name; string: &db_service.name

# List with references
all_services; list[Service]: [&api_service, &db_service]
first_service_name; string: &all_services[0].name
"""
    result = parse_tacl_content(content)
    assert result["api_port"] == 8080
    assert result["db_name"] == "database"
    assert result["first_service_name"] == "api"
    assert len(result["all_services"]) == 2
    print("✓ References with typed objects work")


def test_complex_example():
    """Test a complex example combining all features."""
    print("\n=== Testing Complex Example ===")

    content = """
@type Endpoint:
  path; string
  method; literal["GET", "POST", "PUT", "DELETE"]
  auth_required; bool

@type Service:
  name; string
  port; int
  endpoints; list[Endpoint]
  environment; literal["dev", "staging", "prod"]

# API Service
api; Service:
  name; string: "api-gateway"
  port; int: 8080
  environment; literal["dev", "staging", "prod"]: "prod"
  endpoints; list[Endpoint]: [
    {path: "/users", method: "GET", auth_required: true},
    {path: "/login", method: "POST", auth_required: false}
  ]

# Configuration using union types
timeout; union[int, null]: 30
retry_count; union[int, null]: null

# Reference API details
api_prod_port; int: &api.port
first_endpoint_path; string: &api.endpoints[0].path
"""
    result = parse_tacl_content(content)
    assert result["api"]["name"] == "api-gateway"
    assert result["api"]["environment"] == "prod"
    assert len(result["api"]["endpoints"]) == 2
    assert result["api"]["endpoints"][0]["method"] == "GET"
    assert result["timeout"] == 30
    assert result["retry_count"] is None
    assert result["api_prod_port"] == 8080
    assert result["first_endpoint_path"] == "/users"
    print("✓ Complex example works")


def run_all_tests():
    """Run all test functions."""
    print("Running TACL Feature Tests...")

    try:
        test_literal_types()
        test_union_types()
        test_custom_types()
        test_object_syntax()
        test_references_with_types()
        test_complex_example()

        print("\n✅ All tests passed!")
        return True
    except Exception as e:
        print(f"\n❌ Test failed: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
