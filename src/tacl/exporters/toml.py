"""TOML exporter for TACL files.

This module provides functionality to export TACL configurations to TOML format.
Note that TOML has some limitations compared to TACL:
- No support for null values (automatically omitted)
- All keys must be strings
- Limited support for complex nested structures
"""

from __future__ import annotations

from tacl.parser import parse_tacl_content


class TOMLExportError(Exception):
    """Error during TOML export."""


class TACLTOMLExporter:
    """Export TACL data to TOML format."""

    def __init__(self) -> None:
        """Initialize the TOML exporter."""
        self.warnings: list[str] = []

    def export(self, data: dict[str, object]) -> str:
        """Export TACL data to TOML string.

        Args:
            data: Parsed TACL data dictionary

        Returns:
            TOML formatted string

        Raises:
            TOMLExportError: If TOML export fails
        """
        try:
            import toml
        except ImportError as error:
            raise TOMLExportError(
                "toml package not installed. Install with: pip install toml"
            ) from error

        # Filter out None values as TOML doesn't support null
        cleaned_data = self._clean_nulls(data)

        try:
            return toml.dumps(cleaned_data)
        except Exception as error:
            raise TOMLExportError(f"Failed to export to TOML: {error}") from error

    def _clean_nulls(self, obj: object) -> object:
        """Recursively remove null values from data structure.

        Args:
            obj: Data structure to clean

        Returns:
            Cleaned data structure without nulls
        """
        if isinstance(obj, dict):
            cleaned = {}
            for key, value in obj.items():
                cleaned_value = self._clean_nulls(value)
                if cleaned_value is not None:
                    cleaned[key] = cleaned_value
                else:
                    self.warnings.append(f"Omitted null value for key: {key}")
            return cleaned

        if isinstance(obj, list):
            return [self._clean_nulls(item) for item in obj if item is not None]

        return obj


def compile_tacl_to_toml(tacl_content: str) -> str:
    """Compile TACL content to TOML format.

    This is a convenience function that parses TACL content and exports to TOML.

    Args:
        tacl_content: TACL source content

    Returns:
        TOML formatted string

    Raises:
        ParseError: If TACL parsing fails
        ValidationError: If type validation fails
        TOMLExportError: If TOML conversion fails
    """
    try:
        # Parse TACL content
        parsed_data = parse_tacl_content(tacl_content)

        # Export to TOML
        exporter = TACLTOMLExporter()
        toml_output = exporter.export(parsed_data)

        # Print warnings if any
        if exporter.warnings:
            print("TOML Export Warnings:")
            for warning in exporter.warnings:
                print(f"  - {warning}")

        return toml_output

    except Exception as error:
        raise TOMLExportError(f"TACL compilation failed: {error}") from error
