# TACL-Python

TypeSafe Application Configuration Language - Python library for parsing and compiling TACL files

## Overview

TACL (TypeSafe Application Configuration Language) is a configuration language that brings type safety, references, and better tooling to application configuration. This Python package provides:

- **Parser**: Load and validate TACL files with full type checking
- **Compiler**: Convert TACL to YAML, JSON, or TOML formats
- **API**: Programmatic access to TACL parsing and validation
- **CLI**: Command-line tool for compiling TACL files

## Features

- **Type Safety**: Strong typing with compile-time validation
- **References**: Variable references with circular dependency detection
- **Multiple Output Formats**: Export to YAML, JSON, or TOML
- **Clear Error Messages**: Detailed error reporting with line numbers
- **Python API**: Easy integration into Python applications
- **Extensible**: Custom type definitions and validation rules

## Installation

```bash
pip install tacl
```

For development:
```bash
pip install tacl[dev]
```

## Quick Start

### Command Line Usage

```bash
# Compile TACL to YAML (default)
tacl compile config.tacl

# Compile to JSON
tacl compile config.tacl --format json

# Compile to TOML
tacl compile config.tacl --format toml

# Specify output file
tacl compile config.tacl -o output.yaml

# Validate only (no output)
tacl compile config.tacl --validate-only
```

### Python API Usage

```python
import tacl

# Load TACL file
config = tacl.load("config.tacl")

# Load from string
config = tacl.loads("""
name: string = "MyApp"
port: int = 8080
""")

# Validate TACL file
tacl.validate("config.tacl")

# Validate TACL string
tacl.validate_string("""
name: string = "MyApp"
port: int = 8080
""")
```

## TACL Language Syntax

### Basic Types

```tacl
# String
name: string = "MyApp"

# Integer
port: int = 8080

# Boolean
debug: bool = true

# Float
version: float = 1.5

# Null
optional_value: null = null
```

### Collections

```tacl
# List
ports: list[int] = [8080, 8081, 8082]

# Dictionary
database: dict[string, string] = {
  host: "localhost"
  user: "admin"
  password: "secret"
}
```

### Type Annotations

```tacl
# Optional types
api_key: optional[string] = null

# Union types (enums)
environment: ("dev" | "staging" | "prod") = "dev"

# Custom types
type User = {
  name: string
  email: string
  age: int
}

admin: User = {
  name: "Admin"
  email: "admin@example.com"  
  age: 30
}
```

### References

```tacl
app_name: string = "MyApp"
version: string = "1.0.0"

# Simple reference
title: string = &app_name

# Embedded reference
description: string = "Welcome to &app_name v&version"

# Nested reference
database: dict[string, string] = {
  host: "localhost"
  port: "5432"
}
connection_string: string = "postgresql://&database.host:&database.port"
```

### Multiline Strings

```tacl
# Literal style (preserves newlines)
description: string = |
  This is a multiline
  string that preserves
  line breaks.

# Folded style (folds into a single line)
summary: string = >
  This is a multiline
  string that will be
  folded into one line.
```

## Type System

TACL supports the following types:

- **Primitive Types**: `string`, `int`, `bool`, `float`, `null`
- **Collection Types**: `list[T]`, `dict[K, V]`
- **Optional Types**: `optional[T]` (can be null)
- **Union Types**: `("option1" | "option2" | "option3")`
- **Custom Types**: User-defined object types

## Error Handling

TACL provides detailed error messages:

```
Error at line 5: Type mismatch
Expected type 'int', got 'string' for field 'port'
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/tacl-lang/tacl-python.git
cd tacl-python

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests with coverage
pytest

# Run specific test file
pytest tests/test_parser.py

# Run with verbose output
pytest -v
```

### Code Quality

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Type checking
mypy .

# Security scan
bandit -r src/

# Find dead code
vulture src/
```

## Contributing

Contributions are welcome! Please see the main TACL repository for contribution guidelines.

## License

MIT License - see LICENSE file for details.

## Links

- [Main TACL Repository](https://github.com/tacl-lang/tacl)
- [TACL Specification](https://github.com/tacl-lang/tacl/blob/main/docs/SPECIFICATION.md)
- [VS Code Extension](https://github.com/tacl-lang/vscode-tacl)