"""TACL (Type-Annotated Configuration Language) - A configuration language with type safety.

This module provides a Python API for parsing and working with TACL files.
TACL is a configuration language that combines YAML's readability with
static typing and advanced features like references and custom types.

Example:
    >>> import tacl
    >>> config = tacl.load('config.tacl')
    >>> print(config['server']['port'])
    8080

    >>> from tacl import loads
    >>> data = loads('name; string: "Example"')
    >>> print(data['name'])

Example:
"""

from tacl.api import load, loads, validate, validate_string
from tacl.cli import compile_to_json, compile_to_toml, compile_to_yaml
from tacl.parser import ParseError, TACLParser, TACLReferenceError, ValidationError

__version__ = "0.1.0"
__all__ = [
    # Main API functions
    "load",
    "loads",
    "validate",
    "validate_string",
    # Compilation functions
    "compile_to_yaml",
    "compile_to_json",
    "compile_to_toml",
    # Parser and exceptions
    "TACLParser",
    "ParseError",
    "ValidationError",
    "TACLReferenceError",
]
