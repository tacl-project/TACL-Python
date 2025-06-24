"""TACL to JSON Exporter.

Converts parsed TACL data to JSON format with handling for JSON limitations.
"""

from json import dumps as json_dumps
from sys import exit as sys_exit
from sys import stderr as sys_stderr

from tacl.parser import parse_tacl_content
from tacl.utils import check_return, type_check


class JSONExportError(Exception):
    """Error during JSON export."""

    def __init__(self, message: str) -> None:
        """Initialize JSON export error."""
        type_check(message, str, "message")
        super().__init__(message)
        self.message = message


class TACLJSONExporter:
    """Exporter for converting TACL to JSON format."""

    def __init__(self) -> None:
        """Initialize JSON exporter."""
        self.warnings: list[str] = []
        check_return(None, type(None), "TACLJSONExporter.__init__")

    def _check_json_compatibility(self, value: object, path: str = "root") -> object:
        """Check and convert value for JSON compatibility.

        Args:
            value: The value to check
            path: Current path for error reporting

        Returns:
            JSON-compatible value

        Raises:
            JSONExportError: If value cannot be represented in JSON
        """
        type_check(value, object, "value")
        type_check(path, str, "path")

        # Handle None
        if value is None:
            return check_return(None, type(None), "_check_json_compatibility")

        # Handle JSON primitive types explicitly
        if isinstance(value, str):
            return check_return(value, str, "_check_json_compatibility")

        if isinstance(
            value, bool
        ):  # Check bool before int since bool is subclass of int
            return check_return(value, bool, "_check_json_compatibility")

        if isinstance(value, int):
            return check_return(value, int, "_check_json_compatibility")

        if isinstance(value, float):
            return check_return(value, float, "_check_json_compatibility")

        # Handle lists
        if isinstance(value, list):
            result = []
            for index, item in enumerate(value):
                item_path = f"{path}[{index}]"
                converted_item = self._check_json_compatibility(item, item_path)
                result.append(converted_item)
            return check_return(result, list, "_check_json_compatibility")

        # Handle dictionaries
        if isinstance(value, dict):
            result = {}
            for key, dict_value in value.items():
                # JSON only supports string keys
                if not isinstance(key, str):
                    warning = f"Converting non-string key '{key}' to string at {path}"
                    self.warnings.append(warning)
                    str_key = str(key)
                else:
                    str_key = key

                value_path = f"{path}.{str_key}"
                converted_value = self._check_json_compatibility(dict_value, value_path)
                result[str_key] = converted_value
            return check_return(result, dict, "_check_json_compatibility")

        # Handle other types by converting to string with warning
        warning = f"Converting unsupported type {type(value).__name__} to string at {path}: {value}"
        self.warnings.append(warning)
        string_value = str(value)
        return check_return(string_value, str, "_check_json_compatibility")

    def export_to_json(self, data: dict[str, object], indent: int = 2) -> str:
        """Export TACL data to JSON format.

        Args:
            data: Parsed TACL data
            indent: JSON indentation level

        Returns:
            JSON string

        Raises:
            JSONExportError: If export fails
        """
        type_check(data, dict, "data")
        type_check(indent, int, "indent")

        try:
            # Reset warnings
            self.warnings = []

            # Convert to JSON-compatible format
            json_data = self._check_json_compatibility(data)

            # Generate JSON
            json_output = json_dumps(
                json_data, indent=indent, ensure_ascii=False, sort_keys=True
            )

            # Add warnings as comments (JSON doesn't support comments, so add as header)
            if self.warnings:
                warning_header = "// JSON Export Warnings:\n"
                for warning in self.warnings:
                    warning_header += f"// WARNING: {warning}\n"
                warning_header += "// (Comments not supported in JSON - this is informational only)\n\n"
                json_output = warning_header + json_output

            return check_return(json_output, str, "export_to_json")

        except (TypeError, ValueError) as json_error:
            raise JSONExportError(
                f"Failed to serialize to JSON: {json_error}"
            ) from json_error


def compile_tacl_to_json(tacl_content: str, indent: int = 2) -> str:
    """Compile TACL content directly to JSON.

    Args:
        tacl_content: TACL source content
        indent: JSON indentation level

    Returns:
        JSON string

    Raises:
        JSONExportError: If compilation or export fails
    """
    type_check(tacl_content, str, "tacl_content")
    type_check(indent, int, "indent")

    try:
        # Parse TACL content using shared parser
        parsed_data = parse_tacl_content(tacl_content)

        # Export to JSON
        exporter = TACLJSONExporter()
        json_result = exporter.export_to_json(parsed_data, indent)

        # Print warnings to stderr
        if exporter.warnings:
            print("JSON Export Warnings:", file=sys_stderr)
            for warning in exporter.warnings:
                print(f"  {warning}", file=sys_stderr)

        return json_result

    except Exception as error:
        if isinstance(error, JSONExportError):
            raise
        raise JSONExportError(f"TACL compilation failed: {error}") from error


if __name__ == "__main__":
    # Simple test
    test_tacl = """
# Test TACL to JSON conversion
app_name; string: "Test App"
port; int: 8080
debug; bool: true
timeout; float: 30.5
nullable; null: null
tags; list[string]: ["web", "api", "service"]
config; dict[string, string]: {env: "prod", region: "us-east-1"}
"""

    try:
        json_output = compile_tacl_to_json(test_tacl)
        print("JSON Output:")
        print(json_output)
    except JSONExportError as json_error:
        print(f"JSON Export Error: {json_error}", file=sys_stderr)
        sys_exit(1)
