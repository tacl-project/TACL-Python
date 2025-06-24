#!/usr/bin/env python3
"""TACL CLI - Command Line Interface for TACL Compiler.

Lightweight wrapper around the core tacl module providing CLI functionality
and compilation features.
"""

import sys
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from pathlib import Path

from yaml import YAMLError
from yaml import dump as yaml_dump

import tacl.api
from tacl.parser import ParseError, TACLLoadError, parse_tacl_content
from tacl.utils import type_check


def compile_to_yaml(content: str) -> str:
    """Compile TACL content to YAML format.

    Args:
        content: TACL content as string

    Returns:
        YAML string with references resolved

    Raises:
        ParseError: If syntax is invalid
        ValidationError: If types don't validate
        TACLReferenceError: If references can't be resolved
    """
    type_check(content, str, "content")

    # Convert to YAML
    try:
        return yaml_dump(
            parse_tacl_content(content),
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=True,
        )
    except YAMLError as yaml_error:
        raise ParseError(f"Failed to serialize to YAML: {yaml_error}") from yaml_error


def compile_to_json(content: str, indent: int = 2) -> str:
    """Compile TACL content to JSON format.

    Args:
        content: TACL content as string
        indent: JSON indentation level

    Returns:
        JSON string with references resolved

    Raises:
        ParseError: If syntax is invalid
        ValidationError: If types don't validate
        TACLReferenceError: If references can't be resolved
    """
    type_check(content, str, "content")
    type_check(indent, int, "indent")

    try:
        from tacl.exporters.json import compile_tacl_to_json

        return compile_tacl_to_json(content, indent)
    except ImportError as import_error:
        raise TACLLoadError("JSON export module not available") from import_error


def compile_to_toml(content: str) -> str:
    """Compile TACL content to TOML format.

    Args:
        content: TACL content as string

    Returns:
        TOML string with references resolved

    Raises:
        ParseError: If syntax is invalid
        ValidationError: If types don't validate
        TACLReferenceError: If references can't be resolved
    """
    type_check(content, str, "content")

    try:
        from tacl.exporters.toml import compile_tacl_to_toml

        return compile_tacl_to_toml(content)
    except ImportError as import_error:
        raise TACLLoadError("TOML export module not available") from import_error


def create_argument_parser() -> ArgumentParser:
    """Create and configure argument parser with subcommands."""
    parser = ArgumentParser(
        description="TACL - TypeSafe Application Markup Language",
        formatter_class=RawDescriptionHelpFormatter,
        epilog="""
Examples:
  tacl compile values.tacl                           # Output YAML to values.yaml
  tacl compile values.tacl --format json             # Output JSON to values.json
  tacl compile values.tacl --format toml -o config.toml  # Output TOML to config.toml
  tacl compile values.tacl --validate-only           # Just validate
        """,
    )

    # Create subparsers
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Compile subcommand
    compile_parser = subparsers.add_parser(
        "compile",
        help="Compile TACL to other formats",
        formatter_class=RawDescriptionHelpFormatter,
        epilog="""
Examples:
  tacl compile values.tacl                           # Output YAML to values.yaml
  tacl compile values.tacl --format json             # Output JSON to values.json
  tacl compile values.tacl --format toml -o config.toml  # Output TOML to config.toml
  tacl compile values.tacl --validate-only           # Just validate
        """,
    )

    compile_parser.add_argument("input_file", help="Input TACL file")
    compile_parser.add_argument(
        "-o", "--output", help="Output file (default: input_file.{format})"
    )
    compile_parser.add_argument(
        "--format",
        choices=["yaml", "json", "toml"],
        default="yaml",
        help="Output format (default: yaml)",
    )
    compile_parser.add_argument(
        "--validate-only", action="store_true", help="Only validate, don't output"
    )
    compile_parser.add_argument(
        "--strict", action="store_true", help="Strict validation mode"
    )
    compile_parser.add_argument(
        "--json-indent", type=int, default=2, help="JSON indentation level (default: 2)"
    )

    return parser


def handle_compile_command(args: object) -> None:
    """Handle the compile subcommand."""
    try:
        # Read input file
        with open(args.input_file, encoding="utf-8") as input_file:  # type: ignore[attr-defined]
            tacl_content = input_file.read()

        if args.validate_only is True:  # type: ignore[attr-defined]
            # Just validate
            tacl.validate_string(tacl_content)
            print(f"✅ {args.input_file} is valid TACL")  # type: ignore[attr-defined]
        else:
            # Compile to requested format
            if args.format == "yaml":  # type: ignore[attr-defined]
                output_content = compile_to_yaml(tacl_content)
                format_name = "YAML"
            elif args.format == "json":  # type: ignore[attr-defined]
                output_content = compile_to_json(tacl_content, args.json_indent)  # type: ignore[attr-defined]
                format_name = "JSON"
            elif args.format == "toml":  # type: ignore[attr-defined]
                output_content = compile_to_toml(tacl_content)
                format_name = "TOML"
            else:
                print(f"❌ Error: Unsupported format '{args.format}'", file=sys.stderr)  # type: ignore[attr-defined]
                sys.exit(1)

            # Determine output file
            if args.output is not None:  # type: ignore[attr-defined]
                output_file_path = args.output  # type: ignore[attr-defined]
            else:
                # Generate default output filename: input_file.{format}
                input_path = Path(args.input_file)  # type: ignore[attr-defined]
                output_file_path = str(input_path.with_suffix(f".{args.format}"))  # type: ignore[attr-defined]

            with open(output_file_path, "w", encoding="utf-8") as output_file:
                output_file.write(output_content)
            print(
                f"✅ Compiled {args.input_file} -> {output_file_path} ({format_name})"
            )  # type: ignore[attr-defined]

    except FileNotFoundError:
        print(f"❌ Error: File '{args.input_file}' not found", file=sys.stderr)  # type: ignore[attr-defined]
        sys.exit(1)
    except (
        tacl.TACLError,
        tacl.ValidationError,
        tacl.ParseError,
        tacl.TACLReferenceError,
    ) as tacl_error:
        print(f"❌ Error: {tacl_error}", file=sys.stderr)
        sys.exit(1)
    except Exception as unexpected_error:
        print(f"❌ Unexpected error: {unexpected_error}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """Main entry point."""
    parser = create_argument_parser()
    args = parser.parse_args()

    # Handle subcommands
    if args.command == "compile":
        handle_compile_command(args)
    else:
        # No subcommand provided, show help
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
