# General Imports
import json
from typing import Union
# Module Imports
from src.iot.core import Device
from src.utils.data_utils import load_configs


class DeviceCardano(Device):
    """
    Class implementation for IoT device interacting with Cardano interfaces

    Attributes
    ----------
    _device_id: str
        Unique identifier for the device.
    _metadata: dict
        Configuration values necessary for operations.
    _functions_enums: list
        List of functions to be accessed during operations.
        Should contain only Enums such as in `scr.iot.commands`
    """

    from src.iot.commands import Keysfunctions, WalletFunctions, \
        NodeFunctions, IotExtensionFunctions
    # To-do: Only import if not loaded
    _device_id: str
    _metadata: dict
    _functions_list: list

    def __init__(self, id: str,
                 functions: list = [Keysfunctions, WalletFunctions,
                                    NodeFunctions, IotExtensionFunctions]) \
            -> None:
        """
        Constructor for DeviceCardano class.

        Parameters
        ------
        device_id: str
            Unique identifier for the device.
        """
        self._device_id = id
        self._metadata = None
        self._functions_list = functions
        super().__init__()

    @property
    def device_id(self) -> str:
        return self._device_id

    @property
    def metadata(self) -> dict:
        """
        Get the current metadata.
        """
        return self._metadata

    @metadata.setter
    def metadata(self, vals: Union[str, dict]) -> None:
        """
        Set a valid metadata parameter.

        Parameters
        ---------
        vals: Optional[str, dict]
            The parameters to be set. If str it should be an json
            file to be read. Else, an already loaded python
            dictionary.
        """
        self._metadata = load_configs(vals)

    def message_treatment(self, message) -> dict:
        """
        Main function to handle double way traffic of IoT Service.

        Parameters
        -----
        message: core.Message
            Message object containing the necessary information for
            its processing.

        Returns
        -------
        main: dict
            Information containing the results of the command
            passed down through the message.
        """
        try:
            super().validate_message(message)
            super().validate_inputs(message.payload)
        except AssertionError:
            print('Invalid Message Object')
        main = {'client_id': message.client_id}
        cmd = message.payload['cmd'].upper()
        func = [f for funcs in self._functions_list
                for n, f in funcs.items() if n == cmd][0]
        if not func:
            raise ValueError("The specified command does not exists")
        if message.payload['args']:
            params = func(message.payload['args'])
        else:
            params = func()
        if isinstance(params, list) or isinstance(params, tuple):
            p = {f"output_{v}": params[v] for v in range(len(params))}
            main.update(p)
        elif isinstance(params, dict):
            main.update(params)
        else:
            try:
                from_json = json.loads(params)
                main.update(from_json)
            except ValueError:
                print("There was an error returning your result")
        return main
