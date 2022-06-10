# General imports
import logging
from typing import Union
import json

# Module imports
from src.utils.path_utils import validate_path


def check_nested_dicts(vals: dict):
    """
    Check if a dictionary is nested.
    """
    if any(isinstance(v, dict) for v in vals.values()):
        return True
    else:
        return False


def flatten_dict(input_dict, deep: bool = False):
    """
    Reduce dictionary to only one nested level
    """
    output = []
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


def validate_vars(keywords: list, input_vars: dict, mandatory: bool = False) -> list:
    """
    Complementing `validate_dict` and implemented
    at `parse_inputs`.

    TO DO:
    Missing to annotate/distinguish between optional and necessary arguments
    """
    result = []
    for key, val in input_vars.items():
        try:
            assert val is not None and key in keywords
            result.append(val)
        except AssertionError:
            if mandatory:
                print(f'Provide a valid input for {key}')
                result = []
                break
            else:
                result.append(None)
                continue
    return result


def validate_dict(keywords: list, vals: Union[str, dict]):
    """
    Complementing `validate_vars` and implemented
    at `parse_inputs`.
    """
    if isinstance(vals, str):
        try:
            with open(vals) as f:
                output = json.load(f)
                return output
        except FileNotFoundError:
            try:
                output = json.loads(vals)
                return output
            except TypeError:
                print('Provide a valid format for JSON.')
                return None
    else:
        try:
            output = [val for arg in vals for name, val in arg.items()
                      if name in keywords]
            return output
        except AttributeError:
            print('Provide a valid input')
            return None


def parse_inputs(keywords: list, fill: bool = False, *args, **kwargs):
    """
    Parse the input for Cardano objects functions.
    """
    if args:
        output = validate_dict(keywords, args[0])
        if isinstance(output, dict):
            return [val for key, val in output.items()]
        else:
            return output
    else:
        return validate_vars(keywords, kwargs, fill)


def load_configs(vals: Union[str, dict], full_flat: bool) -> dict:
    """
    Loads configuration files into a dictionary to be use for reading configs
    """
    output: dict
    if isinstance(vals, str):
        try:
            with open(validate_path(vals, False)) as file:
                output = json.load(file)
                if check_nested_dicts(output):
                    output = flatten_dict(output, full_flat)
        except FileNotFoundError:
            logging.error('The provided file was not found')
    elif isinstance(vals, dict):
        output = vals
        if check_nested_dicts(output):
            output = flatten_dict(output, full_flat)
    else:
        raise TypeError('Not supported configuration\'s input')
    return output


def extract_functions(input_class):
    """
    Get functions list from a given class object
    """
    raw_methods = dir(input_class)
    return [func for func in raw_methods if callable(getattr(input_class, func))
            and func.startswith('_') is False]
