"""
Utils submodule for data preprocessing and other data related operations.
"""

# General imports
import logging
from typing import Any, Union, Optional
import json


def check_for_json(input_str: str) -> Union[dict, str]:
    """
    Determines if a string is just a string or can be load as dict.

    Parameters
    ----------
    input_str: str
        THe input string to be check.

    Returns
    -------
    out: Union[dict, str]
        Returns a dict if is possible to decode the string as JSON else returns
        the same string.
    """
    if isinstance(input_str, str):
        try:
            out = json.loads(input_str)
        except json.JSONDecodeError:
            out = input_str
    else:
        raise TypeError(f'The input {input_str} is not a string.')
    return out


def check_nested_dicts(vals: dict) -> bool:
    """
    Check if a dictionary is nested.

    Parameters
    ---------
    vals: dict
        The dictionary to be checked if its nested or not.

    Returns
    ------
    bool
        Either `True` or `False` if the dictionary is nested or not.
    """
    if any(isinstance(v, dict) for v in vals.values()):
        return True
    else:
        return False


def flatten_dict(input_dict: dict, deep: Optional[bool] = False) -> dict:
    """
    Reduce dictionary to only one nested level

    Parameters
    ----------
    input_dict: dict
        The dictionary to be flatten.
    deep: Optional[bool], default = False
        If the dictionary should have at least one nested level or not.

    Returns
    -------
    dict
        The resulting flattened dictionary.
    """
    output: list[tuple[Any, Any]] = []
    for key, val in input_dict.items():
        if deep:
            try:
                output.extend(flatten_dict(val).items())
            except AttributeError:
                output.append((key, val))
        else:
            try:
                if check_nested_dicts(val):
                    output.extend(flatten_dict(val).items())
                else:
                    output.append((key, val))
            except AttributeError:
                output.append((key, val))
    return dict(output)


def unpack_kwargs(vals: dict, keywords: list,
                  fill: Optional[bool] = True) -> dict:
    """
    Unpack a set of **kwargs given based on a set of keywords provided.

    Parameters
    ----------
    vals: dict
        `**kwargs` comming down from the function call.
    keywords: Optional[list], default = []
        Set of target variables to look for.
    fill: bool, default = True
        If a set of keywords are given and you want to unpack that specific
        number of variables, you can fill them with `None`.

    Returns
    -------
    result: dict
        Resulting dictionary of unpackage process.
    """
    result: dict[Any, Any] = {}
    if not vals:
        return result
    for key, val in vals.items():
        if isinstance(val, str) and key in keywords:
            result[key] = check_for_json(val)
        elif not isinstance(val, str) and key in keywords:
            result[key] = val
    result = _clear_duplicates(result)
    diff = set(keywords).difference(set(result.keys()))
    if (len(diff) > 0) and fill:
        for key in diff:
            result[key] = None
    return result


def unpack_args(vals: tuple, keywords: list,
                fill: Optional[bool] = True) -> dict:
    """
    Unpack a set of *args given based on a set of keywords provided.

    Parameters
    ----------
    vals: tuple[Any]
        `*args` comming down from the function call.
    keywords: Optional[list], default = []
        Set of target variables to look for.
    fill: bool, default = True
        If a set of keywords are given and you want to unpack that specific
        number of variables, you can fill them with `None`.

    Returns
    -------
    output: dict
        Resulting dictionary of unpackage process.
    """
    output: dict[Any, Any] = {}
    if not vals:
        return output
    elif len(keywords) < len(vals):
        _vars = vals[:int(len(keywords) - len(vals))]
    else:
        _vars = vals
    for i in range(len(keywords)):
        try:
            if isinstance(_vars[i], str):
                output[keywords[i]] = check_for_json(_vars[i])
            else:
                output[keywords[i]] = _vars[i]
        except IndexError:
            if fill:
                output[keywords[i]] = None
            else:
                break
    output = _clear_duplicates(output)
    return output


def _clear_duplicates(input_val: dict) -> dict:
    """
    Helper function that checks wether keys are repeated inside and outside
    the input dictionary.

    Parameters
    ----------
    input_val: dict
        Dictionary to be checked.

    Returns
    -------
    dict
        Dictionary already cleaned.
    """
    to_check = [n for n, v in input_val.items() if isinstance(v, dict)]
    for key in to_check:
        try:
            temp_keys = input_val[key].keys()
            coincidences = set(input_val.keys()).intersection(set(temp_keys))
            if len(coincidences) > 0:
                new_vals = {c: input_val[key][c] for c in coincidences}
            input_val.update(new_vals)
        except AttributeError:
            break
    return input_val


def parse_inputs(keywords: list[str], strict: bool = False,
                 _args: Optional[tuple[Any]] = None,
                 _kwargs: Optional[dict[Any, Any]] = None) -> list:
    """
    Parse *args and **kwargs for a functions that requires specific variables
    to work.

    Parameters
    ---------
    keywords: list[str]
        List of variable names to look for.
    strict: bool, default = False
        Signal if all the keywords must have a value other than `None`.
    *args , **kwargs
        Refers to all the values to be passed down this function.

    Returns
    -------
    list
        Resulting list of values that can be unpacked onto local variables.
    """
    unpacked_args: dict[Any, Any]
    unpacked_kwargs: dict[Any, Any]

    if not _args:
        unpacked_args = unpack_args((), keywords)
    else:
        unpacked_args = unpack_args(_args, keywords)
    if not _kwargs:
        unpacked_kwargs = unpack_kwargs({}, keywords)
    else:
        unpacked_kwargs = unpack_kwargs(_kwargs, keywords)
    stage = flatten_dict({**unpacked_args, **unpacked_kwargs})
    if strict and (set(stage.keys()) != set(keywords)):
        raise KeyError(f'The following requested keywords are missing: \
            {set(stage.keys()).difference(set(keywords))}')
    return [stage[k] for k in keywords]


def load_configs(vals: Union[str, dict], full_flat: bool) -> dict:
    """
    Loads configuration files into a dictionary to be use for reading configs

    Parameters
    ----------
    vals: Union[str, dict]
        Input parameter to load configurations.
    full_flat: bool
        If the output dictionary should contain only one level or not.

    Returns
    -------
    dict:
        The loaded dictionary containing the key, value from the given input.
    """
    output: dict
    if isinstance(vals, str):
        try:
            with open(vals) as file:
                output = json.load(file)
                if check_nested_dicts(output):
                    output = flatten_dict(output, full_flat)
            return output
        except FileNotFoundError:
            logging.error('The provided file was not found')
    elif isinstance(vals, dict):
        output = vals
        if check_nested_dicts(output):
            output = flatten_dict(output, full_flat)
        return output
    else:
        raise TypeError('Not supported configuration\'s input')
    return {}


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
