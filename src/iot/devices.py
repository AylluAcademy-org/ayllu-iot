# General Imports
import json
import logging
from typing import Union
# Module Imports
from src.iot.core import Device
from src.utils.path_utils import get_root_path
from src.utils.data_utils import check_nested_dicts, flatten_dict

working_dir = get_root_path()


class DeviceIot(Device):
    # Pending implementation
    def __init__(self):
        pass


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

    from src.iot.commands import WalletFunctions, NodeFunctions, \
        IotExtensionFunctions
    # To-do: Only import if not loaded
    device_id: str
    metadata: dict
    functions_list: list

    def __init__(self, id: str,
                 functions: list = [WalletFunctions, NodeFunctions,
                                    IotExtensionFunctions]) -> None:
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
        if isinstance(vals, str):
            try:
                with open(f'{working_dir}/{vals}') as file:
                    self._metadata = json.load(file)
                    if check_nested_dicts(self._metadata):
                        self._metadata = flatten_dict(self._metadata)
            except FileNotFoundError:
                logging.error('The provided file was not found')
        elif isinstance(vals, dict):
            self._metadata = vals
            if check_nested_dicts(self._metadata):
                self._metadata = flatten_dict(self._metadata)
        else:
            logging.error('Not supported configuration\'s input')

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
            super().validate_inputs(message.message)
        except AssertionError:
            print('Invalid Message Object')
        main = {'client_id': message.client_id}
        cmd = message.message['cmd'].upper()
        func = [f for funcs in self._functions_list
                for n, f in funcs.items() if n == cmd][0]
        if not func:
            raise ValueError("The command does not exists")
        if message.message['args']:
            params = func(message.message['args'])
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
