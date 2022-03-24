# General imports
import json
from enum import Enum
# Package imports
from src.iot.devices import DeviceCardano
from src.cardano.utils import parse_inputs

def basic_math(*args, **kwargs) -> list:
    """
    return_list: bool, default=False
    """

    print('Executing Basic Math')
    return_list = parse_inputs(['return_list'], args, kwargs)

    a = 2 + 2
    b = 2 * 2
    c = 2 ** 2
    
    if return_list:
        return [a, b, c]
    else:
        return (a, b, c)

def basic_dict() -> dict:
    return {'status': 'successful'}

def basic_json(input_dict: dict):
    return json.dumps(input_dict)

class TestDeviceCardanoFunctionsOne(Enum):
    """
    Enum loaded with testing functions for DeviceCardano
    with numerical values
    """
    BASIC_MATH = basic_math

class TestDeviceCardanoFunctionsTwo(Enum):
    """
    Enum loaded with testing functions for DeviceCardano
    with text values
    """
    BASIC_DICT = basic_dict
    BASIC_JSON = basic_json

# If necessary could add another Enum for other type of functions

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

    _device_id: str
    _metadata: dict
    _functions_enums: list

    def __init__(self, device_id: str):
        """
        Constructor for TestDeviceCardano class.

        Parameters
        ------
        device_id: str
            Unique identifier for the device.
        """
        super(DeviceCardano, self).__init__(device_id)
        self._device_id = super(DeviceCardano, self)._device_id
        self._metadata = super(DeviceCardano, self)._metadata
        self._functions_enums = [TestDeviceCardanoFunctionsOne, TestDeviceCardanoFunctionsTwo]