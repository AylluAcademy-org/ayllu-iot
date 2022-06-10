# General imports
import json
from typing import Any, Union
# Package imports
from src.iot.devices import DeviceCardano
from src.utils.data_utils import extract_functions, parse_inputs


class TestDCFuncsOne:

    def __init__(self, input_configs):
        pass

    def basic_math(self, *args, **kwargs):  # -> Union[list[int], tuple]
        """
        return_list: bool, default=False
        """

        print('Executing Basic Math')
        print(f"Printing *kwargs: {kwargs}")
        return_list = parse_inputs(['return_list'], False, args, kwargs)

        a = 2 + 2
        b = 2 * 2
        c = 2 ** 2

        if return_list:
            return [a, b, c]
        else:
            return (a, b, c)


class TestDCFuncsTwo:

    def __init__(self, input_configs):
        pass

    def basic_dict(self) -> dict:
        """
        """
        return {'status': 'successful'}

    def basic_json(self, input_dict: dict):
        """
        """
        return json.dumps(input_dict)


class TestDeviceCardano(DeviceCardano):
    """
    Extension of class for testing purposes. As functions had their
    own tests, we  just need to check for manipulation and call.

    Attributes
    ---------
    _device_id: str
        Unique identifier for the device.
    _metadata: dict
        Configuration values necessary for operations.
    _functions_enums: list
        List of functions to be accessed during operations.
        Should contain only Enums such as in `scr.iot.commands`
    """

    def __init__(self, device_id: str):
        """
        Constructor for TestDeviceCardano class.

        Parameters
        ------
        device_id: str
            Unique identifier for the device.
        """
        super().__init__(self_id=device_id, executors_list=['TestDCFuncsOne', 'TestDCFuncsTwo'])

    def _initialize_classes(self, classes_list: list, set_configs: Union[str, dict]) -> dict:
        initialized_objects: dict[Any, list[str]] = {}
        for obj in classes_list:
            if obj == 'TestDCFuncsOne':
                funcs_one = TestDCFuncsOne(set_configs)
                initialized_objects[funcs_one] = extract_functions(funcs_one)
            elif obj == 'TestDCFuncsTwo':
                funcs_two = TestDCFuncsTwo(set_configs)
                initialized_objects[funcs_two] = extract_functions(funcs_two)
            else:
                raise KeyError('Specified object is not implemented for this Device')
        return initialized_objects
