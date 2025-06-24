"""TACL Functions - Shared utility functions for TACL modules.

This module contains utility functions that are used across multiple TACL modules
but are not part of the core parser functionality.
"""

from typing import Any, Dict, Tuple, Type, TypeVar, Union, get_args, get_origin

T = TypeVar('T')


def type_check(
    value: Any,
    expected_type: Type[Any],
    param_name: str = "value",
) -> bool:
    """Runtime type checking function with comprehensive validation.

    Args:
        value: The value to check
        expected_type: The expected type (can be basic types, unions, generics)
        param_name: Name of parameter for error messages

    Returns:
        True if type matches, False otherwise

    Raises:
        TypeError: If type check fails with detailed error message
    """
    # Handle None type
    if expected_type is type(None) or expected_type is None:
        if value is not None:
            raise TypeError(f"{param_name}: expected None, got {type(value).__name__}")
        return True

    # Handle Union types (e.g., str | int, Optional[str]) first
    origin = get_origin(expected_type)
    
    # Handle basic types (str, int, bool, float) if no origin
    if origin is None and isinstance(expected_type, type):
        if not isinstance(value, expected_type):
            raise TypeError(
                f"{param_name}: expected {expected_type.__name__}, got {type(value).__name__}"
            )
        return True
    if origin is not None:
        args = get_args(expected_type)

        # Handle Union/Optional types
        if str(origin) in ("<class 'types.UnionType'>", "typing.Union"):
            for arg_type in args:
                try:
                    if type_check(value, arg_type, param_name):
                        return True
                except TypeError:
                    continue
            # If no union member matches, raise error
            type_names = [getattr(arg, "__name__", str(arg)) for arg in args]
            raise TypeError(
                f"{param_name}: expected one of {type_names}, got {type(value).__name__}"
            )

        # Handle list types (list[str], etc.)
        if origin is list:
            if not isinstance(value, list):
                raise TypeError(
                    f"{param_name}: expected list, got {type(value).__name__}"
                )
            if len(args) > 0:
                item_type = args[0]
                for index, item in enumerate(value):
                    type_check(item, item_type, f"{param_name}[{index}]")
            return True

        # Handle dict types (dict[str, int], etc.)
        if origin is dict:
            if not isinstance(value, dict):
                raise TypeError(
                    f"{param_name}: expected dict, got {type(value).__name__}"
                )
            if len(args) >= 2:
                key_type, value_type = args[0], args[1]
                for dict_key, dict_value in value.items():
                    type_check(dict_key, key_type, f"{param_name}.key")
                    type_check(dict_value, value_type, f"{param_name}[{dict_key}]")
            return True

    # If we can't determine the type, assume it's valid
    # This handles complex types that we can't easily introspect
    return True


def check_params(**kwargs: Tuple[Any, Type[Any]]) -> None:
    """Helper to check multiple parameters at once.
    
    Args:
        **kwargs: Parameter name to (value, expected_type) tuple mapping
    """
    for name, (value, expected_type) in kwargs.items():
        type_check(value, expected_type, name)


def check_return(
    value: T,
    expected_type: Type[T],
    function_name: str = "function",
) -> T:
    """Check return value type and return the value if valid.
    
    Args:
        value: The value to check and return
        expected_type: The expected type of the value
        function_name: Name of the function for error messages
        
    Returns:
        The original value if type check passes
        
    Raises:
        TypeError: If the value doesn't match the expected type
    """
    type_check(value, expected_type, f"{function_name} return value")
    return value
