# General imports
import logging
from typing import Union
import json


def check_nested_dicts(vals: dict):
    """
    Check if a dictionary is nested.
    """
    if any(isinstance(v, dict) for v in vals.values()):
        return True
    else:
        return False


def flatten_dict(d, parent_key='', sep=''):
    """
    Credits to:
    stackoverflow.com
    /questions/6027558/flatten-nested-dictionaries-compressing-keys#6027615
    """
    items = []
    for k, v in d.items():
        nk = str(k) if parent_key else k
        try:
            items.extend(flatten_dict(v, nk, sep=sep).items())
        except AttributeError:
            items.append((nk, v))
    return dict(items)


def validate_vars(keywords: list, input_vars: dict) -> list:
    """
    Complementing `validate_dict` and implemented
    at `parse_inputs`.

    TO DO:
    Missing to annotate/distinguish between optional and necessary arguments
    """
    for key, val in input_vars.items():
        try:
            assert val is not None and key in keywords
        except AssertionError:
            print(f'Provide a valid input for {key}')
    return vars.values()


def validate_dict(keywords: list, vals: Union[str, dict]) \
        -> Union[dict, list]:
    """
    Complementing `validate_vars` and implemented
    at `parse_inputs`.
    """
    if isinstance(vals, str):
        try:
            with open(vals) as f:
                from_json = json.load(f)
                return from_json
        except FileNotFoundError:
            try:
                from_json = json.loads(vals)
                return from_json
            except TypeError:
                print('Provide a valid format for JSON.')
    else:
        try:
            return [val for arg in vals for name, val in arg.items()
                    if name in keywords]
        except AttributeError:
            print('Provide a valid input')


def parse_inputs(keywords: list, *args, **kwargs):
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
        return validate_vars(keywords, kwargs)


def load_configs(vals: Union[str, dict]):
    """
    Loads configuration files into a dictionary to be use for reading configs
    """
    if isinstance(vals, str):
        try:
            with open(vals) as file:
                output = json.load(file)
                if check_nested_dicts(output):
                    output = flatten_dict(output)
            return output
        except FileNotFoundError:
            logging.error('The provided file was not found')
    elif isinstance(vals, dict):
        output = vals
        if check_nested_dicts(output):
            output = flatten_dict(output)
        return output
    else:
        logging.error('Not supported configuration\'s input')
