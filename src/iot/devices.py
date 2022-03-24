# General Imports
import json
import logging
from typing import Union
# Module Imports
from src.iot.core import Device
from src.iot.commands import IotExtensionFunctions, NodeFunctions, \
                            WalletFunctions
from src.utils.path_utils import get_root_path
from src.utils.data_utils import check_nested_dicts, flatten_dict

working_dir = get_root_path()
class DeviceIot(Device):
    # Pending implementation
    def __init__(self):
        pass

class DeviceCardano(Device):
    """
    Class implementation for IoT device interacting with Cardano 
    interfaces

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
    _device_id: str
    _metadata: dict
    _functions_enums: list

    def __init__(self, device_id: str) -> None:
        """
        Constructor for DeviceCardano class.

        Parameters
        ------
        device_id: str
            Unique identifier for the device.
        """
        super(Device, self).__init__(device_id)
        self._device_id = device_id
        self._metadata = None
        self._functions_enums = [WalletFunctions, NodeFunctions, \
                                IotExtensionFunctions]

    @property
    def _metadata(self) -> dict:
        """
        Get the current metadata.
        """
        return self._metadata
    
    @_metadata.setter
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
                with open(working_dir + vals) as file:
                    self.metadata=json.loads(file)
                    if check_nested_dicts(self.metadata):
                        self.metadata = flatten_dict(self.metadata)
            except FileNotFoundError:
                logging.error('The provided file was not found')
        elif isinstance(vals, dict):
            self.metadata=vals
            if check_nested_dicts(self.metadata):
                self.metadata = flatten_dict(self.metadata)
        else:
            logging.error('Not supported configuration\'s input')

    @property
    def _functions_enums(self) -> list:
        """
        Get the current functions available for operations.
        """
        return self._functions_enums

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
            super.validate_message(message)
            super.validate_inputs(message.message)
        except AssertionError:
            print('Invalid Message Object')
        main = {'client_id': message.client_id}
        cmd = message.message['cmd'].upper()
        func = [o.cmd for o in self._functions_enums \
                for f in o if f == cmd]
        if not func:
            raise ValueError("The command does not exists")
        if message.message['args']:
            params = func(message.message['args'])
        else:
            params = func()
        if isinstance(list, params) or isinstance(tuple, params):
            p = {f"output_{v}": params[v] for v in range(len(params))}
            main.update(p)
        elif isinstance(dict, params):
            main.update(params)
        else:
            try:
                from_json = json.loads(params)
                main.update(from_json)
            except ValueError:
                print("There was an error returning your result")
        return main