"""TACL - TypeSafe Application Markup Language.

This module provides the core API for loading and working with TACL files in Python.
It contains only the essential user-facing functions for loading TACL content.
"""

from pathlib import Path

from tacl.parser import (
    ParseError,
    TACLError,
    TACLField,
    TACLLoadError,
    TACLParser,
    TACLReference,
    TACLReferenceError,
    TACLType,
    TypeKind,
    ValidationError,
    parse_tacl_content,
)
from tacl.utils import type_check


def load(file_path: str | Path) -> dict[str, object]:
    """Load a TACL file and return the parsed Python object.

    Args:
        file_path: Path to the TACL file

    Returns:
        Dictionary containing the parsed TACL data with references resolved

    Raises:
        TACLLoadError: If the file cannot be loaded or parsed
        FileNotFoundError: If the file does not exist
        ValidationError: If the TACL content has validation errors
        ParseError: If the TACL content has syntax errors
        TACLReferenceError: If there are reference resolution errors
    """
    type_check(file_path, str | Path, "file_path")

    try:
        # Convert to Path object for consistent handling
        path = Path(file_path) if isinstance(file_path, str) else file_path

        # Read the file
        with path.open(encoding="utf-8") as f:
            content = f.read()

        # Parse and return the result
        return parse_tacl_content(content)

    except FileNotFoundError:
        raise
    except (ValidationError, ParseError, TACLReferenceError):
        raise
    except Exception as error:
        raise TACLLoadError(
            f"Failed to load TACL file '{file_path}': {error}"
        ) from error


def loads(content: str) -> dict[str, object]:
    """Load TACL content from a string and return the parsed Python object.

    Args:
        content: TACL content as a string

    Returns:
        Dictionary containing the parsed TACL data with references resolved

    Raises:
        TACLLoadError: If the content cannot be parsed
        ValidationError: If the TACL content has validation errors
        ParseError: If the TACL content has syntax errors
        TACLReferenceError: If there are reference resolution errors
    """
    type_check(content, str, "content")

    try:
        return parse_tacl_content(content)
    except (ValidationError, ParseError, TACLReferenceError):
        raise
    except Exception as error:
        raise TACLLoadError(f"Failed to parse TACL content: {error}") from error


def validate(file_path: str | Path) -> bool:
    """Validate a TACL file without loading it.

    Args:
        file_path: Path to the TACL file

    Returns:
        True if the file is valid TACL

    Raises:
        FileNotFoundError: If the file does not exist
        ValidationError: If the TACL content has validation errors
        ParseError: If the TACL content has syntax errors
        TACLReferenceError: If there are reference resolution errors
    """
    type_check(file_path, str | Path, "file_path")

    # Validation is the same as loading - if it loads successfully, it's valid
    load(file_path)
    return True


def validate_string(content: str) -> bool:
    """Validate TACL content from a string without loading it.

    Args:
        content: TACL content as a string

    Returns:
        True if the content is valid TACL

    Raises:
        ValidationError: If the TACL content has validation errors
        ParseError: If the TACL content has syntax errors
        TACLReferenceError: If there are reference resolution errors
    """
    type_check(content, str, "content")

    # Validation is the same as loading - if it loads successfully, it's valid
    loads(content)
    return True


# Re-export the core classes and exceptions for convenience
__all__ = [
    "ParseError",
    "TACLError",
    "TACLField",
    "TACLLoadError",
    "TACLParser",
    "TACLReference",
    "TACLReferenceError",
    "TACLType",
    "TypeKind",
    "ValidationError",
    "load",
    "loads",
    "validate",
    "validate_string",
]
