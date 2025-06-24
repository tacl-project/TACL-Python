"""TACL to YAML Exporter.

Converts parsed TACL data to YAML format with full TACL feature support.
"""

from sys import exit as sys_exit
from sys import stderr as sys_stderr

from yaml import YAMLError, safe_load
from yaml import dump as yaml_dump

from tacl.parser import TACLField, TACLParser
from tacl.utils import check_return, type_check


class YAMLExportError(Exception):
    """Error during YAML export."""

    def __init__(self, message: str) -> None:
        """Initialize YAML export error."""
        type_check(message, str, "message")
        super().__init__(message)
        self.message = message


class TACLYAMLExporter:
    """Exporter for converting TACL to YAML format."""

    def __init__(self) -> None:
        """Initialize YAML exporter."""
        # YAML is the native format, so no compatibility warnings needed
        check_return(None, type(None), "TACLYAMLExporter.__init__")

    def export_to_yaml(self, data: dict[str, object]) -> str:
        """Export TACL data to YAML format.

        Args:
            data: Parsed TACL data

        Returns:
            YAML string

        Raises:
            YAMLExportError: If export fails
        """
        type_check(data, dict, "data")

        try:
            # YAML is the native format for TACL, so no conversion needed
            yaml_output = yaml_dump(
                data, default_flow_style=False, allow_unicode=True, sort_keys=True
            )
            return check_return(yaml_output, str, "export_to_yaml")

        except YAMLError as yaml_error:
            raise YAMLExportError(
                f"Failed to serialize to YAML: {yaml_error}"
            ) from yaml_error


def compile_tacl_to_yaml(tacl_content: str) -> str:
    """Compile TACL content directly to YAML.

    This function extracts the YAML compilation logic from the main taclc module
    to follow the same pattern as JSON and TOML exporters.

    Args:
        tacl_content: TACL source content

    Returns:
        YAML string

    Raises:
        YAMLExportError: If compilation or export fails
    """
    type_check(tacl_content, str, "tacl_content")

    try:
        # Parse TACL using existing parser
        parser = TACLParser()

        lines = tacl_content.split("\n")
        fields: list[TACLField] = []

        # First pass: Parse all fields, handling multiline blocks
        line_index = 0
        while line_index < len(lines):
            line = lines[line_index]
            line_num = line_index + 1

            # Skip comments and empty lines
            if not line.strip() or line.strip().startswith("#"):
                line_index += 1
                continue

            # Check if this line has a TACL type annotation
            match = parser.type_pattern.match(line.strip())
            if match is None:
                line_index += 1
                continue

            key = match.group(1).strip()
            type_str = match.group(2).strip()
            value_str = match.group(3).strip()

            # Check if this is a multiline block
            if value_str.endswith(("|", ">", "|-", ">-", "|+", ">+")):
                # Parse the multiline block
                yaml_block, end_line = parser.parse_multiline_block(lines, line_index)
                try:
                    value = safe_load(yaml_block)
                except YAMLError as yaml_error:
                    raise YAMLExportError(
                        f"Invalid YAML multiline block on line {line_num}: {yaml_error}"
                    ) from yaml_error

                line_index = end_line + 1
            else:
                # Regular single-line value
                try:
                    value = safe_load(value_str)
                except YAMLError as yaml_error:
                    raise YAMLExportError(
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
        parsed_data: dict[str, object] = {}
        for field in fields:
            parsed_data[field.key] = field.value

        # Second pass: Resolve references and validate
        resolved_yaml_lines: list[str] = []
        line_index = 0

        while line_index < len(lines):
            line = lines[line_index]
            line_num = line_index + 1

            # Check if this line has a TACL type annotation
            match = parser.type_pattern.match(line.strip())
            if match is None:
                # Keep comments and structure lines as-is
                resolved_yaml_lines.append(line)
                line_index += 1
                continue

            # Find the corresponding field
            key = match.group(1).strip()
            field = None
            for f in fields:
                if f.key == key:
                    field = f
                    break

            if field is None:
                # This shouldn't happen if parsing worked correctly
                resolved_yaml_lines.append(line)
                line_index += 1
                continue

            # Resolve references in the field value
            try:
                resolved_value = parser.resolve_references_in_value(
                    field.value, parsed_data
                )
            except Exception as ref_error:
                raise YAMLExportError(f"Line {line_num}: {ref_error}") from ref_error

            # Validate the resolved value
            try:
                parser.validate_value(resolved_value, field.type_annotation, field.key)
            except Exception as validation_error:
                raise YAMLExportError(
                    f"Line {field.line_number}: {validation_error}"
                ) from validation_error

            # Check if this was a multiline block
            value_str = match.group(3).strip()
            if value_str.endswith(("|", ">", "|-", ">-", "|+", ">+")):
                # Skip the multiline content lines
                _, end_line = parser.parse_multiline_block(lines, line_index)
                line_index = end_line + 1

                # Generate the YAML output with the resolved value
                yaml_value = yaml_dump(resolved_value).strip()
                resolved_yaml_lines.append(f"{field.key}: {yaml_value}")
            else:
                # Regular single-line value
                yaml_value = yaml_dump(resolved_value).strip()
                resolved_yaml_lines.append(f"{field.key}: {yaml_value}")
                line_index += 1

        result = "\n".join(resolved_yaml_lines)
        return check_return(result, str, "compile_tacl_to_yaml")

    except Exception as error:
        if isinstance(error, YAMLExportError):
            raise
        raise YAMLExportError(f"TACL compilation failed: {error}") from error


if __name__ == "__main__":
    # Simple test
    test_tacl = """
# Test TACL to YAML conversion
app_name; string: "Test App"
port; int: 8080
debug; bool: true
timeout; float: 30.5
nullable; optional[string]: null
tags; list[string]: ["web", "api", "service"]
config; dict[string, string]: {env: "prod", region: "us-east-1"}

# Reference test
main_app; string: "&app_name"
web_port; int: "&port"
"""

    try:
        yaml_output = compile_tacl_to_yaml(test_tacl)
        print("YAML Output:")
        print(yaml_output)
    except YAMLExportError as yaml_error:
        print(f"YAML Export Error: {yaml_error}", file=sys_stderr)
        sys_exit(1)
