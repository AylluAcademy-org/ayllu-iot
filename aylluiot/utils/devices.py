"""
Utils submodule for helpers functions use inside devices definitions.
"""

# General imports
from typing import Any, Optional

def extract_functions(input_class: Any, built_ins: bool = False) \
        -> Optional[list[str]]:
    """
    Get functions list from a given class object

    Parameters
    ---------
    input_class: Any
        The given object to be used.
    built_ins: bool, default = False
        Either to accept or not built-in objects such as `int` or `str`.

    Returns
    -------
    list[str]
        List of public methods name for the given object.
    """
    raw_methods: Optional[list[str]]

    if built_ins:
        raw_methods = dir(input_class)
    else:
        raw_methods = dir(input_class) if type(input_class) not in \
            [str, int, float, list, dict, tuple, set] else None
    if raw_methods:
        out = [func for func in raw_methods
               if callable(getattr(input_class, func))
               and func.startswith('_') is False]
    else:
        raise TypeError('The given class is a built-in type. Either change the\
            function call to accept built_ins or provide other input class.')
    return out
