"""TACL Parser - Core parsing functionality for TACL files.

This module contains the parser, type system, and core classes for TACL.
It does not include high-level API functions or compilation utilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from re import Match, Pattern, sub
from re import compile as re_compile
from typing import Any, Union

from yaml import YAMLError, safe_load

from tacl.utils import check_return, type_check

# Type aliases for bulletproof typing
TACLValue = Union[str, int, float, bool, None, list[Any], dict[str, Any]]
TACLData = dict[str, TACLValue]


class TACLError(Exception):
    """Base exception for TACL parsing errors."""

    def __init__(self, message: str) -> None:
        """Initialize TACL error with message."""
        type_check(message, str, "message")
        super().__init__(message)
        self.message = message
        check_return(None, type(None), "TACLError.__init__")


class ValidationError(TACLError):
    """Type validation error."""


class ParseError(TACLError):
    """Parse error in TACL syntax."""


class TACLReferenceError(TACLError):
    """Reference resolution error."""


class TACLLoadError(TACLError):
    """Error loading TACL file or content."""

    def __init__(self, message: str) -> None:
        """Initialize TACL load error."""
        type_check(message, str, "message")
        super().__init__(message)
        self.message = message


class TypeKind(Enum):
    """Enumeration of all supported TACL types."""

    STRING = "string"
    INT = "int"
    BOOL = "bool"
    FLOAT = "float"
    NULL = "null"
    LIST = "list"
    DICT = "dict"
    OPTIONAL = "optional"
    UNION = "union"
    LITERAL = "literal"
    CUSTOM = "custom"
    OBJECT = "object"


@dataclass(frozen=True)
class TACLType:
    """Immutable representation of a TACL type annotation."""

    kind: TypeKind
    inner_type: "TACLType | None" = None
    key_type: "TACLType | None" = None
    union_types: list["TACLType"] | None = None
    literal_values: list[str] | None = None
    custom_name: str | None = None

    def __post_init__(self) -> None:
        """Validate type construction invariants."""
        if self.kind == TypeKind.OPTIONAL and self.inner_type is None:
            raise ParseError("Optional type must have inner_type")
        if self.kind == TypeKind.LIST and self.inner_type is None:
            raise ParseError("List type must have inner_type")
        if self.kind == TypeKind.DICT and (
            self.key_type is None or self.inner_type is None
        ):
            raise ParseError("Dict type must have key_type and inner_type")
        if self.kind == TypeKind.UNION and (
            self.union_types is None or len(self.union_types) == 0
        ):
            raise ParseError("Union type must have union_types")
        if self.kind == TypeKind.LITERAL and (
            self.literal_values is None or len(self.literal_values) == 0
        ):
            raise ParseError("Literal type must have literal_values")
        if self.kind == TypeKind.CUSTOM and (
            self.custom_name is None or len(self.custom_name) == 0
        ):
            raise ParseError("Custom type must have custom_name")


@dataclass(frozen=True)
class TACLField:
    """Immutable representation of a parsed TACL field."""

    key: str
    type_annotation: TACLType
    value: TACLValue
    line_number: int


@dataclass(frozen=True)
class TACLReference:
    """Immutable representation of a TACL reference."""

    path: str
    line_number: int


@dataclass(frozen=True)
class TypeDefinition:
    """Immutable representation of a custom type definition."""

    name: str
    fields: dict[str, TACLType]
    line_number: int


class TACLParser:
    """Parser for TACL files with strict type safety."""

    def __init__(self) -> None:
        """Initialize TACL parser with compiled regex patterns."""
        # Regex patterns compiled once for performance
        type_pattern = re_compile(r"^([^;]+);\s*([^:]+):\s*(.*)$")
        reference_pattern = re_compile(r"&([a-zA-Z_][a-zA-Z0-9_.[\]]*)")
        type_definition_pattern = re_compile(r"^@type\s+([a-zA-Z_][a-zA-Z0-9_]*):\s*$")

        type_check(type_pattern, Pattern[str], "type_pattern")
        type_check(reference_pattern, Pattern[str], "reference_pattern")
        type_check(type_definition_pattern, Pattern[str], "type_definition_pattern")

        self.type_pattern: Pattern[str] = type_pattern
        self.reference_pattern: Pattern[str] = reference_pattern
        self.type_definition_pattern: Pattern[str] = type_definition_pattern

        # State for tracking parsed values and references
        self.parsed_values: TACLData = {}
        self.pending_references: list[TACLReference] = []
        self.custom_types: dict[str, TypeDefinition] = {}

        check_return(None, type(None), "TACLParser.__init__")

    def _parse_value_with_references(self, value_str: str, line_num: int) -> TACLValue:
        """Parse a value that contains references, handling them specially."""
        value_str = value_str.strip()
        
        # Handle list syntax [&ref1, &ref2, "literal", 123]
        if value_str.startswith("[") and value_str.endswith("]"):
            # Parse as list, preserving references
            list_content = value_str[1:-1].strip()
            if not list_content:
                return []
            
            items = []
            # Simple split by comma (not handling nested structures for now)
            for item in list_content.split(","):
                item = item.strip()
                if item.startswith("&"):
                    # Keep reference as string
                    items.append(item)
                else:
                    # Parse as normal YAML value
                    try:
                        items.append(safe_load(item))
                    except YAMLError as yaml_error:
                        raise ParseError(
                            f"Invalid item in list on line {line_num}: {yaml_error}"
                        ) from yaml_error
            return items
        
        # Handle object syntax {key: &ref, key2: "value"}
        elif value_str.startswith("{") and value_str.endswith("}"):
            # For now, fall back to YAML parsing and let references fail
            # This is a complex case that would need proper parsing
            try:
                return safe_load(value_str)
            except YAMLError as yaml_error:
                raise ParseError(
                    f"Invalid object value on line {line_num}: {yaml_error}"
                ) from yaml_error
        
        # Single reference
        elif value_str.startswith("&"):
            return value_str
        
        # String with embedded references
        else:
            # For strings like "Hello &name", keep as-is for later resolution
            return value_str

    def _parse_multiline_array(self, lines: list[str], start_index: int) -> tuple[list[TACLValue], int]:
        """Parse a multiline array that starts with [ and ends with ]."""
        type_check(lines, list, "lines")
        type_check(start_index, int, "start_index")
        
        items: list[TACLValue] = []
        current_line = start_index
        array_content_lines: list[str] = []
        
        # Collect all lines until we find the closing ]
        while current_line < len(lines):
            line = lines[current_line]
            stripped = line.strip()
            
            # Skip empty lines and comments
            if not stripped or stripped.startswith("#"):
                current_line += 1
                continue
                
            # Check if this line contains the closing ]
            if "]" in stripped:
                # Add content up to the ]
                bracket_index = stripped.find("]")
                before_bracket = stripped[:bracket_index].strip()
                if before_bracket:
                    array_content_lines.append(before_bracket)
                break
            else:
                # Add the full line content
                array_content_lines.append(stripped)
            
            current_line += 1
        
        # Parse the collected array content as YAML
        if array_content_lines:
            # Join all content and parse as array items
            full_content = "\n".join(array_content_lines)
            
            # Try to parse each item (they should be YAML-like objects)
            for line in array_content_lines:
                line = line.strip()
                if line.endswith(","):
                    line = line[:-1].strip()
                
                if line.startswith("{") and line.endswith("}"):
                    # Parse as YAML object
                    try:
                        item = safe_load(line)
                        items.append(item)
                    except YAMLError as yaml_error:
                        raise ParseError(
                            f"Invalid array item on line {start_index + len(items) + 1}: {yaml_error}"
                        ) from yaml_error
                elif line.startswith("&"):
                    # Reference
                    items.append(line)
                elif line:
                    # Try to parse as any YAML value
                    try:
                        item = safe_load(line)
                        items.append(item)
                    except YAMLError as yaml_error:
                        raise ParseError(
                            f"Invalid array item on line {start_index + len(items) + 1}: {yaml_error}"
                        ) from yaml_error
        
        result = (items, current_line + 1)
        return check_return(result, tuple, "_parse_multiline_array")

    def parse_type(self, type_str: str) -> TACLType:
        """Parse a type string into TACLType with full validation."""
        type_check(type_str, str, "type_str")
        type_str = type_str.strip()

        if (len(type_str) == 0) is True:
            raise ParseError("Empty type annotation")

        # Handle optional types: optional[string]
        if (type_str.startswith("optional[") is True) and (
            type_str.endswith("]") is True
        ):
            inner_type_str = type_str[9:-1]
            if (len(inner_type_str) == 0) is True:
                raise ParseError("Optional type cannot be empty")
            inner_type = self.parse_type(inner_type_str)
            result = TACLType(kind=TypeKind.OPTIONAL, inner_type=inner_type)
            return check_return(result, TACLType, "parse_type")

        # Handle list types: list[string]
        if (type_str.startswith("list[") is True) and (type_str.endswith("]") is True):
            inner_type_str = type_str[5:-1]
            if (len(inner_type_str) == 0) is True:
                raise ParseError("List type cannot be empty")
            inner_type = self.parse_type(inner_type_str)
            result = TACLType(kind=TypeKind.LIST, inner_type=inner_type)
            return check_return(result, TACLType, "parse_type")

        # Handle dict types: dict[string, string] or dict[string]
        if (type_str.startswith("dict[") is True) and (type_str.endswith("]") is True):
            dict_inner = type_str[5:-1]
            if (len(dict_inner) == 0) is True:
                raise ParseError("Dict type cannot be empty")

            if ("," in dict_inner) is True:
                parts = dict_inner.split(",", 1)
                if (len(parts) != 2) is True:
                    raise ParseError("Dict type must have exactly one comma")
                key_type_str = parts[0].strip()
                value_type_str = parts[1].strip()
                if ((len(key_type_str) == 0) or (len(value_type_str) == 0)) is True:
                    raise ParseError("Dict key and value types cannot be empty")
                key_type = self.parse_type(key_type_str)
                value_type = self.parse_type(value_type_str)
                result = TACLType(
                    kind=TypeKind.DICT, key_type=key_type, inner_type=value_type
                )
                return check_return(result, TACLType, "parse_type")
            # dict[string] - shorthand for dict[string, string]
            value_type = self.parse_type(dict_inner.strip())
            string_type = TACLType(kind=TypeKind.STRING)
            result = TACLType(
                kind=TypeKind.DICT, key_type=string_type, inner_type=value_type
            )
            return check_return(result, TACLType, "parse_type")

        # Handle literal types: literal["debug", "info", "warn", "error"] or literal[200, 404, 500]
        if (type_str.startswith("literal[") is True) and (
            type_str.endswith("]") is True
        ):
            literal_inner = type_str[8:-1]
            if (len(literal_inner) == 0) is True:
                raise ParseError("Literal type cannot be empty")

            literal_values: list[str] = []
            # Split by comma but respect quotes
            current_value = ""
            in_quotes = False
            escape_next = False

            for char in literal_inner:
                if escape_next:
                    current_value += char
                    escape_next = False
                elif char == "\\":
                    escape_next = True
                    current_value += char
                elif char == '"':
                    in_quotes = not in_quotes
                    current_value += char
                elif char == "," and not in_quotes:
                    # End of value
                    value = current_value.strip()
                    if len(value) > 0:
                        literal_values.append(value)
                    current_value = ""
                else:
                    current_value += char

            # Add the last value
            value = current_value.strip()
            if len(value) > 0:
                literal_values.append(value)

            if (len(literal_values) == 0) is True:
                raise ParseError("Literal type must have at least one value")

            result = TACLType(kind=TypeKind.LITERAL, literal_values=literal_values)
            return check_return(result, TACLType, "parse_type")

        # Handle union types: union[string, int] or union[int, float, null]
        if (type_str.startswith("union[") is True) and (type_str.endswith("]") is True):
            union_inner = type_str[6:-1]
            if (len(union_inner) == 0) is True:
                raise ParseError("Union type cannot be empty")

            union_types: list[TACLType] = []
            parts = union_inner.split(",")

            for part_raw in parts:
                part = part_raw.strip()
                if (len(part) == 0) is True:
                    raise ParseError("Union type parts cannot be empty")
                union_type = self.parse_type(part)
                union_types.append(union_type)

            if (len(union_types) == 0) is True:
                raise ParseError("Union type must have at least one type")

            result = TACLType(kind=TypeKind.UNION, union_types=union_types)
            return check_return(result, TACLType, "parse_type")

        # Handle primitive types
        if type_str == "string":
            result = TACLType(kind=TypeKind.STRING)
            return check_return(result, TACLType, "parse_type")
        if type_str == "int":
            result = TACLType(kind=TypeKind.INT)
            return check_return(result, TACLType, "parse_type")
        if type_str == "bool":
            result = TACLType(kind=TypeKind.BOOL)
            return check_return(result, TACLType, "parse_type")
        if type_str == "float":
            result = TACLType(kind=TypeKind.FLOAT)
            return check_return(result, TACLType, "parse_type")
        if type_str == "null":
            result = TACLType(kind=TypeKind.NULL)
            return check_return(result, TACLType, "parse_type")
        if type_str == "object":
            result = TACLType(kind=TypeKind.OBJECT)
            return check_return(result, TACLType, "parse_type")
        # Custom type (struct-like)
        if (not type_str.isidentifier()) is True:
            raise ParseError(f"Invalid custom type name: {type_str}")
        result = TACLType(kind=TypeKind.CUSTOM, custom_name=type_str)
        return check_return(result, TACLType, "parse_type")

    def parse_multiline_block(
        self, lines: list[str], start_line: int
    ) -> tuple[str, int]:
        """Parse a multiline YAML block (| or >) and return the complete YAML string."""
        type_check(lines, list, "lines")
        type_check(start_line, int, "start_line")

        if start_line >= len(lines):
            return check_return(
                ("", start_line), tuple[str, int], "parse_multiline_block"
            )

        first_line = lines[start_line].rstrip()
        if not first_line.endswith(("|", ">", "|-", ">-", "|+", ">+")):
            return check_return(
                (first_line, start_line), tuple[str, int], "parse_multiline_block"
            )

        # Extract the multiline indicator
        multiline_indicator = first_line.split(":")[-1].strip()
        yaml_block = [multiline_indicator]

        # Find the base indentation of the content
        content_line_index = start_line + 1
        base_indent = None

        # Skip empty lines to find first content line
        while content_line_index < len(lines):
            line = lines[content_line_index]
            if line.strip():  # Non-empty line
                base_indent = len(line) - len(line.lstrip())
                break
            content_line_index += 1

        if base_indent is None:
            # No content found - empty multiline block
            return check_return(
                (first_line, start_line), tuple[str, int], "parse_multiline_block"
            )

        # Collect all lines that belong to this block
        current_line = start_line + 1
        while current_line < len(lines):
            line = lines[current_line]

            # Empty line - always include
            if not line.strip():
                yaml_block.append(line)
                current_line += 1
                continue

            # Check indentation
            line_indent = len(line) - len(line.lstrip())

            # If line is indented more than or equal to base, it's part of the block
            if line_indent >= base_indent:
                yaml_block.append(line)
                current_line += 1
            else:
                # Line is at same level or outdented - end of block
                break

        result = ("\n".join(yaml_block), current_line - 1)
        return check_return(result, tuple[str, int], "parse_multiline_block")

    def resolve_reference(
        self, ref_path: str, parsed_data: TACLData
    ) -> TACLValue:
        """Resolve a reference path like 'database.host' or 'services[0].name'."""
        type_check(ref_path, str, "ref_path")
        type_check(parsed_data, dict, "parsed_data")

        parts = ref_path.split(".")
        current_value: TACLValue = parsed_data

        for part in parts:
            # Handle array access like 'services[0]'
            if "[" in part and part.endswith("]"):
                array_name = part[: part.index("[")]
                index_str = part[part.index("[") + 1 : -1]
                try:
                    index = int(index_str)
                except ValueError as value_error:
                    raise TACLReferenceError(
                        f"Invalid array index in reference: {part}"
                    ) from value_error

                if (
                    not isinstance(current_value, dict)
                    or array_name not in current_value
                ):
                    raise TACLReferenceError(
                        f"Array '{array_name}' not found in reference path: {ref_path}"
                    )

                array_value = current_value[array_name]
                if not isinstance(array_value, list):
                    raise TACLReferenceError(
                        f"'{array_name}' is not an array in reference: {ref_path}"
                    )

                if index < 0 or index >= len(array_value):
                    raise TACLReferenceError(
                        f"Array index {index} out of bounds in: {ref_path}"
                    )

                current_value = array_value[index]
            else:
                # Regular property access
                if not isinstance(current_value, dict) or part not in current_value:
                    raise TACLReferenceError(
                        f"Property '{part}' not found in reference path: {ref_path}"
                    )
                current_value = current_value[part]

        return current_value

    def resolve_references_in_value(
        self,
        value: TACLValue,
        parsed_data: TACLData,
        visited_refs: set[str] | None = None,
    ) -> TACLValue:
        """Recursively resolve references in a value (dict, list, or primitive)."""
        # Value can be any TACL value type
        type_check(parsed_data, dict, "parsed_data")
        if visited_refs is not None:
            type_check(visited_refs, set, "visited_refs")

        if visited_refs is None:
            visited_refs = set()

        if isinstance(value, dict):
            resolved_dict = {}
            for key, val in value.items():
                resolved_dict[key] = self.resolve_references_in_value(
                    val, parsed_data, visited_refs
                )
            return resolved_dict
        if isinstance(value, list):
            result_list = [
                self.resolve_references_in_value(item, parsed_data, visited_refs)
                for item in value
            ]
            return result_list
        if isinstance(value, str):
            # Check if the entire string is a reference
            if value.startswith("&"):
                # This is a reference - resolve it
                ref_path = value[1:]  # Remove the & prefix

                # Check for circular references
                if ref_path in visited_refs:
                    raise TACLReferenceError(f"Circular reference detected: {ref_path}")

                visited_refs.add(ref_path)
                resolved_value = self.resolve_reference(ref_path, parsed_data)
                # If the resolved value is also a reference, resolve it recursively
                result = self.resolve_references_in_value(
                    resolved_value, parsed_data, visited_refs
                )
                visited_refs.remove(ref_path)
                return result
            if "&" in value:
                # String contains embedded references - replace them

                def replace_ref(match: Match[str]) -> str:
                    ref_path = match.group(1)
                    # Check for circular references
                    if ref_path in visited_refs:
                        raise TACLReferenceError(
                            f"Circular reference detected: {ref_path}"
                        )

                    visited_refs.add(ref_path)
                    try:
                        resolved_ref = self.resolve_reference(ref_path, parsed_data)
                        # Convert to string for embedding
                        if isinstance(resolved_ref, str):
                            result = resolved_ref
                        else:
                            result = str(resolved_ref)
                    except Exception:
                        visited_refs.discard(ref_path)
                        raise
                    else:
                        visited_refs.remove(ref_path)
                        return result

                # Replace all &reference patterns in the string
                # Pattern: &identifier or &object.property or &array[index]
                result_string = sub(
                    r"&([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*(?:\[\d+\])*)",
                    replace_ref,
                    value,
                )
                return result_string
        # Primitive value - return as-is
        # Don't type check the return since TACLValue is a union
        return value

    def validate_value(
        self, value: TACLValue, tacl_type: TACLType, field_path: str
    ) -> None:
        """Validate a value against its TACL type with comprehensive checking."""
        # Value can be any TACL value type
        type_check(tacl_type, TACLType, "tacl_type")
        type_check(field_path, str, "field_path")
        if (tacl_type.kind == TypeKind.OPTIONAL) is True:
            if (value is None) is True:
                return check_return(None, type(None), "validate_value")
            assert tacl_type.inner_type is not None
            self.validate_value(value, tacl_type.inner_type, field_path)
            return check_return(None, type(None), "validate_value")

        if (tacl_type.kind == TypeKind.STRING) is True:
            if (not isinstance(value, str)) is True:
                raise ValidationError(
                    f"{field_path}: expected string, got {type(value).__name__}"
                )

        elif (tacl_type.kind == TypeKind.INT) is True:
            # Explicitly exclude bool since isinstance(True, int) is True in Python
            if ((not isinstance(value, int)) or isinstance(value, bool)) is True:
                raise ValidationError(
                    f"{field_path}: expected int, got {type(value).__name__}"
                )

        elif (tacl_type.kind == TypeKind.BOOL) is True:
            if (not isinstance(value, bool)) is True:
                raise ValidationError(
                    f"{field_path}: expected bool, got {type(value).__name__}"
                )

        elif (tacl_type.kind == TypeKind.FLOAT) is True:
            if (
                (not isinstance(value, int | float)) or isinstance(value, bool)
            ) is True:
                raise ValidationError(
                    f"{field_path}: expected float, got {type(value).__name__}"
                )

        elif (tacl_type.kind == TypeKind.NULL) is True:
            if (value is not None) is True:
                raise ValidationError(f"{field_path}: expected null, got {value}")

        elif (tacl_type.kind == TypeKind.LIST) is True:
            if (not isinstance(value, list)) is True:
                raise ValidationError(
                    f"{field_path}: expected list, got {type(value).__name__}"
                )
            assert tacl_type.inner_type is not None

            # Type guard: we know value is a list now
            assert isinstance(value, list)
            for index, item in enumerate(value):
                item_path = f"{field_path}[{index}]"
                self.validate_value(item, tacl_type.inner_type, item_path)

        elif (tacl_type.kind == TypeKind.DICT) is True:
            if (not isinstance(value, dict)) is True:
                raise ValidationError(
                    f"{field_path}: expected dict, got {type(value).__name__}"
                )
            assert tacl_type.key_type is not None
            assert tacl_type.inner_type is not None

            # Type guard: we know value is a dict now
            assert isinstance(value, dict)
            for dict_key, dict_value in value.items():
                key_path = f"{field_path}.key"
                value_path = f"{field_path}[{dict_key}]"
                self.validate_value(dict_key, tacl_type.key_type, key_path)
                self.validate_value(dict_value, tacl_type.inner_type, value_path)

        elif (tacl_type.kind == TypeKind.LITERAL) is True:
            assert tacl_type.literal_values is not None

            # Check if value matches any literal value
            value_str = str(value) if not isinstance(value, str) else value
            matched = False

            for literal_val in tacl_type.literal_values:
                # Try to parse the literal value to check type compatibility
                if literal_val.startswith('"') and literal_val.endswith('"'):
                    # String literal
                    if isinstance(value, str) and value == literal_val[1:-1]:
                        matched = True
                        break
                else:
                    # Try numeric literals
                    try:
                        if "." in literal_val:
                            # Float literal
                            literal_float = float(literal_val)
                            if (
                                isinstance(value, (int, float))
                                and value == literal_float
                            ):
                                matched = True
                                break
                        else:
                            # Int literal
                            literal_int = int(literal_val)
                            if (
                                isinstance(value, int)
                                and not isinstance(value, bool)
                                and value == literal_int
                            ):
                                matched = True
                                break
                    except ValueError:
                        # Not a numeric literal
                        pass

            if not matched:
                valid_values = ", ".join(tacl_type.literal_values)
                raise ValidationError(
                    f"{field_path}: value '{value}' not in allowed values: {valid_values}"
                )

        elif (tacl_type.kind == TypeKind.UNION) is True:
            assert tacl_type.union_types is not None

            # Try to validate against each union type
            valid = False
            errors = []

            for union_type in tacl_type.union_types:
                try:
                    self.validate_value(value, union_type, field_path)
                    valid = True
                    break
                except ValidationError as validation_error:
                    errors.append(str(validation_error))

            if not valid:
                type_names = []
                for union_type in tacl_type.union_types:
                    if union_type.kind == TypeKind.CUSTOM:
                        type_names.append(union_type.custom_name or "unknown")
                    else:
                        type_names.append(union_type.kind.value)

                raise ValidationError(
                    f"{field_path}: value does not match any union type: {' | '.join(type_names)}"
                )

        elif (tacl_type.kind == TypeKind.OBJECT) is True:
            # Object type accepts any value
            pass

        elif (tacl_type.kind == TypeKind.CUSTOM) is True:
            assert tacl_type.custom_name is not None

            if not isinstance(value, dict):
                raise ValidationError(
                    f"{field_path}: expected object for type {tacl_type.custom_name}"
                )

            # Validate against custom type definition if available
            if (
                hasattr(self, "custom_types")
                and tacl_type.custom_name in self.custom_types
            ):
                type_def = self.custom_types[tacl_type.custom_name]

                # Check all required fields are present and valid
                for field_name, field_type in type_def.fields.items():
                    if field_name not in value:
                        # Check if field is optional
                        if field_type.kind != TypeKind.OPTIONAL:
                            raise ValidationError(
                                f"{field_path}: missing required field '{field_name}' for type {tacl_type.custom_name}"
                            )
                    else:
                        # Validate field value
                        field_path_nested = f"{field_path}.{field_name}"
                        self.validate_value(
                            value[field_name], field_type, field_path_nested
                        )

                # Check for extra fields
                for field_name in value:
                    if field_name not in type_def.fields:
                        raise ValidationError(
                            f"{field_path}: unexpected field '{field_name}' for type {tacl_type.custom_name}"
                        )

        # Validation completed successfully
        return check_return(None, type(None), "validate_value")

    def parse_object_block(
        self, lines: list[str], start_line: int, expected_type: TACLType | None = None
    ) -> tuple[dict[str, TACLValue], int]:
        """Parse an object block with indented field definitions."""
        type_check(lines, list, "lines")
        type_check(start_line, int, "start_line")
        if expected_type is not None:
            type_check(expected_type, TACLType, "expected_type")

        result_object: dict[str, TACLValue] = {}
        current_line = start_line
        base_indent = None

        while current_line < len(lines):
            line = lines[current_line]

            # Skip empty lines and comments
            if not line.strip() or line.strip().startswith("#"):
                current_line += 1
                continue

            # Determine base indentation from first field
            if base_indent is None:
                if line.startswith("  ") or line.startswith("\t"):
                    base_indent = len(line) - len(line.lstrip())
                else:
                    # No indented content - empty object
                    break

            # Check if line is at correct indentation level
            line_indent = len(line) - len(line.lstrip())
            if line_indent < base_indent:
                # End of object block
                break

            # Parse field
            stripped_line = line.strip()
            if ";" in stripped_line and ":" in stripped_line:
                # Field with type: key; type: value
                parts = stripped_line.split(";", 1)
                field_name = parts[0].strip()
                type_and_value = parts[1].strip()

                if ":" in type_and_value:
                    type_parts = type_and_value.split(":", 1)
                    field_type_str = type_parts[0].strip()
                    field_value_str = type_parts[1].strip()

                    # Parse the type
                    field_type = self.parse_type(field_type_str)

                    # Parse the value
                    field_value: TACLValue
                    if field_value_str == "":
                        # Empty value means object block or list follows
                        current_line += 1
                        if current_line < len(lines) and lines[
                            current_line
                        ].strip().startswith("-"):
                            # Parse YAML-style list
                            field_value, current_line = self.parse_yaml_list(
                                lines, current_line
                            )
                        else:
                            # Parse object block
                            field_value, current_line = self.parse_object_block(
                                lines, current_line, field_type
                            )
                        current_line -= (
                            1  # Adjust because we'll increment at end of loop
                        )
                    else:
                        # Parse inline value
                        # Check if it's a reference (starts with &)
                        if field_value_str.strip().startswith("&"):
                            # Keep as string for later reference resolution
                            field_value = field_value_str.strip()
                        elif field_value_str.strip() == "[":
                            # Multiline array starting with [ on its own line
                            current_line += 1
                            field_value, current_line = self._parse_multiline_array(lines, current_line)
                            current_line -= 1  # Adjust because we'll increment at end of loop
                        else:
                            # Check if value contains references (&)
                            if "&" in field_value_str:
                                # This might be a list or value with references - parse carefully
                                field_value = self._parse_value_with_references(field_value_str, current_line + 1)
                            else:
                                try:
                                    field_value = safe_load(field_value_str)
                                except YAMLError as yaml_error:
                                    raise ParseError(
                                        f"Invalid value on line {current_line + 1}: {yaml_error}"
                                    ) from yaml_error

                    result_object[field_name] = field_value
            elif ":" in stripped_line:
                # Simple key: value syntax (no type annotation)
                parts = stripped_line.split(":", 1)
                field_name = parts[0].strip()
                field_value_str = parts[1].strip()

                if field_value_str == "":
                    # Empty value means object block or list follows
                    current_line += 1
                    if current_line < len(lines) and lines[
                        current_line
                    ].strip().startswith("-"):
                        # Parse YAML-style list
                        field_value, current_line = self.parse_yaml_list(
                            lines, current_line
                        )
                    else:
                        # Parse object block
                        field_value, current_line = self.parse_object_block(
                            lines, current_line
                        )
                    current_line -= 1  # Adjust because we'll increment at end of loop
                else:
                    # Parse inline value
                    # Check if it's a reference (starts with &)
                    if field_value_str.strip().startswith("&"):
                        # Keep as string for later reference resolution
                        field_value = field_value_str.strip()
                    elif field_value_str.strip() == "[":
                        # Multiline array starting with [ on its own line
                        current_line += 1
                        field_value, current_line = self._parse_multiline_array(lines, current_line)
                        current_line -= 1  # Adjust because we'll increment at end of loop
                    else:
                        # Check if value contains references (&)
                        if "&" in field_value_str:
                            # This might be a list or value with references - parse carefully
                            field_value = self._parse_value_with_references(field_value_str, current_line + 1)
                        else:
                            try:
                                field_value = safe_load(field_value_str)
                            except YAMLError as yaml_error:
                                raise ParseError(
                                    f"Invalid value on line {current_line + 1}: {yaml_error}"
                                ) from yaml_error

                result_object[field_name] = field_value

            current_line += 1

        return (result_object, current_line)

    def parse_yaml_list(
        self, lines: list[str], start_line: int
    ) -> tuple[list[TACLValue], int]:
        """Parse a YAML-style list with - prefixed items."""
        type_check(lines, list, "lines")
        type_check(start_line, int, "start_line")

        result_list: list[TACLValue] = []
        current_line = start_line
        base_indent = None

        while current_line < len(lines):
            line = lines[current_line]

            # Skip empty lines and comments
            if not line.strip() or line.strip().startswith("#"):
                current_line += 1
                continue

            # Determine base indentation from first list item
            if base_indent is None:
                if line.lstrip().startswith("-"):
                    base_indent = len(line) - len(line.lstrip())
                else:
                    # Not a list item - end of list
                    break

            # Check if line is at correct indentation level
            line_indent = len(line) - len(line.lstrip())
            if line_indent < base_indent:
                # End of list
                break

            # Parse list item
            stripped_line = line.strip()
            if stripped_line.startswith("-"):
                # Remove the dash and parse the value
                item_value_str = stripped_line[1:].strip()

                item_value: TACLValue
                if item_value_str == "":
                    # Multi-line list item (nested object or list)
                    current_line += 1
                    if current_line < len(lines) and lines[
                        current_line
                    ].strip().startswith("-"):
                        # Nested list
                        item_value, current_line = self.parse_yaml_list(
                            lines, current_line
                        )
                    else:
                        # Nested object
                        item_value, current_line = self.parse_object_block(
                            lines, current_line
                        )
                    current_line -= 1  # Adjust because we'll increment at end of loop
                else:
                    # Parse inline value
                    # Check if it's a reference (starts with &)
                    if item_value_str.strip().startswith("&"):
                        # Keep as string for later reference resolution
                        item_value = item_value_str.strip()
                    else:
                        try:
                            # Check for multiline strings
                            if item_value_str.endswith(("|", ">", "|-", ">-", "|+", ">+")):
                                # Create a temporary line for multiline parsing
                                temp_lines = [f"temp: {item_value_str}"] + lines[
                                    current_line + 1 :
                                ]
                                yaml_block, end_offset = self.parse_multiline_block(
                                    temp_lines, 0
                                )
                                item_value = safe_load(yaml_block)
                                current_line += end_offset
                            else:
                                item_value = safe_load(item_value_str)
                        except YAMLError as yaml_error:
                            raise ParseError(
                                f"Invalid value in list on line {current_line + 1}: {yaml_error}"
                            ) from yaml_error

                result_list.append(item_value)

            current_line += 1

        return (result_list, current_line)


def parse_tacl_content(content: str) -> TACLData:
    """Parse TACL content and return resolved data structure.

    Args:
        content: TACL content as string

    Returns:
        Parsed and resolved TACL data

    Raises:
        ParseError: If syntax is invalid
        ValidationError: If types don't validate
        TACLReferenceError: If references can't be resolved
    """
    type_check(content, str, "content")

    parser = TACLParser()
    lines = content.split("\n")
    fields: list[TACLField] = []
    type_definitions: list[TypeDefinition] = []

    # First pass: Parse type definitions and fields
    line_index = 0
    while line_index < len(lines):
        line = lines[line_index]
        line_num = line_index + 1

        # Skip comments and empty lines
        if not line.strip() or line.strip().startswith("#"):
            line_index += 1
            continue

        # Check for @type definition
        type_def_match = parser.type_definition_pattern.match(line.strip())
        if type_def_match is not None:
            type_name = type_def_match.group(1)
            line_index += 1

            # Parse type definition fields
            type_fields: dict[str, TACLType] = {}
            while line_index < len(lines):
                field_line = lines[line_index]

                # Stop at empty line or next definition
                if not field_line.strip() or field_line.strip().startswith("#"):
                    if not field_line.strip():
                        line_index += 1
                        break
                    line_index += 1
                    continue

                # Check if it's a field definition (indented)
                if field_line.startswith("  ") or field_line.startswith("\t"):
                    field_line = field_line.strip()
                    # Parse field: name; type
                    if ";" in field_line:
                        field_parts = field_line.split(";", 1)
                        field_name = field_parts[0].strip()
                        field_type_str = field_parts[1].strip()
                        field_type = parser.parse_type(field_type_str)
                        type_fields[field_name] = field_type
                    line_index += 1
                else:
                    # End of type definition
                    break

            type_def = TypeDefinition(
                name=type_name, fields=type_fields, line_number=line_num
            )
            type_definitions.append(type_def)
            parser.custom_types[type_name] = type_def
            continue

        # Check if this line has a TACL field with type annotation
        match = parser.type_pattern.match(line.strip())
        if match is None:
            line_index += 1
            continue

        key = match.group(1).strip()
        type_str = match.group(2).strip()
        value_str = match.group(3).strip()

        # Check if value is empty (object block or list follows)
        value: TACLValue
        if value_str == "":
            # Check next line to determine if it's a list or object
            line_index += 1
            if line_index < len(lines):
                next_line = lines[line_index]
                if next_line.strip().startswith("-"):
                    # Parse YAML-style list
                    value, line_index = parser.parse_yaml_list(lines, line_index)
                else:
                    # Parse object block
                    value, line_index = parser.parse_object_block(lines, line_index)
            else:
                value = {}
        elif value_str.endswith(("|", ">", "|-", ">-", "|+", ">+")):
            # Parse the multiline block
            yaml_block, end_line = parser.parse_multiline_block(lines, line_index)
            try:
                value = safe_load(yaml_block)
            except YAMLError as yaml_error:
                raise ParseError(
                    f"Invalid YAML multiline block on line {line_num}: {yaml_error}"
                ) from yaml_error

            line_index = end_line + 1
        else:
            # Regular single-line value
            # Check if it's a reference (starts with &)
            if value_str.strip().startswith("&"):
                # Keep as string for later reference resolution
                value = value_str.strip()
            elif value_str.strip() == "[":
                # Multiline array starting with [ on its own line
                line_index += 1
                value, line_index = parser._parse_multiline_array(lines, line_index)
                line_index -= 1  # Will be incremented at the end
            else:
                # Check if value contains references (&) 
                if "&" in value_str:
                    # This might be a list or value with references - parse carefully
                    value = parser._parse_value_with_references(value_str, line_num)
                else:
                    try:
                        value = safe_load(value_str)
                    except YAMLError as yaml_error:
                        raise ParseError(
                            f"Invalid YAML value on line {line_num}: {yaml_error}"
                        ) from yaml_error
            line_index += 1

        # Parse the type and create the field
        type_annotation = parser.parse_type(type_str)
        field = TACLField(
            key=key,
            type_annotation=type_annotation,
            value=value,
            line_number=line_num,
        )
        fields.append(field)

    # Build the parsed data dictionary for reference resolution
    parsed_data: TACLData = {}
    for field in fields:
        parsed_data[field.key] = field.value

    # Second pass: Resolve references and validate
    for field in fields:
        # Resolve references in the field value
        try:
            resolved_value = parser.resolve_references_in_value(
                field.value, parsed_data
            )
        except Exception as ref_error:
            raise TACLReferenceError(
                f"Line {field.line_number}: {ref_error}"
            ) from ref_error

        # Validate the resolved value
        try:
            parser.validate_value(resolved_value, field.type_annotation, field.key)
        except Exception as validation_error:
            raise ValidationError(
                f"Line {field.line_number}: {validation_error}"
            ) from validation_error

        # Update the parsed data with the resolved value for future reference resolution
        parsed_data[field.key] = resolved_value

    return parsed_data
