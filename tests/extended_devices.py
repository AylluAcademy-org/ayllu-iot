"""
Support implementations for different contexts that will help testing out the 
devices objects.
"""

# General imports
import json
from typing import Optional
# Package imports
from aylluiot.utils.data_utils import parse_inputs


class TestDEFuncsOne:

    def __init__(self) -> None:
        """
        Basic Executor for `DeviceExecutor` that contains math operations.
        """
        pass

    def basic_math(self, *args, **kwargs) -> Optional[list[int]]:
        """
        Simple set of math operations that can be modified based.

        Parameters
        ----------
        input_list: list[Any]
            Random list of values.
        expected_list: list[Any]
            Random list of values that could or not be equal to `input_list`
            changing the behaviour of the function based on it.

        Returns
        -------
        Optional[list[int]]
            List of three integers or None.
        """

        print('Executing Basic Math')
        inputed, expected = parse_inputs(['inputed', 'expected'], False,
                                         args, kwargs)
        print(f"Inputed: {inputed}\nExpected: {expected}")

        a = 2 + 2
        b = 2 * 2
        c = 2 ** 2

        if inputed == expected:
            return [a, b, c]
        else:
            return None


class TestDEFuncsTwo:

    def __init__(self) -> None:
        """
        Basic Executor for `DeviceExecutor` that contains string operations.
        """
        pass

    def basic_dict(self) -> dict[str, str]:
        """
        Mimic a standard status dictionary.

        Returns
        -------
        dict[str, str]
            Hard-coded dictionary.
        """
        return {'status': 'successful'}

    def basic_json(self, input_dict: dict) -> str:
        """
        Mimic a basic json serialized value.

        Returns
        -------
        str
            JSON formatted str.
        """
        return json.dumps(input_dict)
