# General Imports
import json
import logging
# Module Imports
from src.iot.core import Device
from src.iot.commands import ExtensionFunctions, NodeFunctions, WalletFunctions
from src.utils.path_utils import get_root_path

working_dir = get_root_path()

class DeviceIot(Device):
    # Pending implementation
    def __init__(self):
        pass

class DeviceCardano(Device):
    """
    Class implementation for IoT device
    interacting with Cardano interfaces

    Parameters
    ----------
    _device_id: str
        Unique identifier for the device.
    _metadata: dict
        Configuration values necessary for operations.
    """
    def __init__(self, device_id: str, metadata: dict=None):
        super(Device, self).__init__(device_id, metadata)
        from src.iot.commands import WalletFunctions, NodeFunctions, ExtensionFunctions

    @property
    def metadata(self):
        """
        Get the current metadata.
        """
        return self._metadata # Maybe limit access to data for security reasons ?
    
    @metadata.setter
    def metadata(self, vals):
        """
        Set a valid metadata parameter.

        Parameters
        ---------
        vals: Optional[str, dict]
            The parameters to be set. If str it should be an json file to be read. Else, an already loaded python dictionary.
        """
        if isinstance(vals, str):
            try:
                with open(working_dir + vals) as file: # 'config/cardano_config.json'
                    self.metadata=json.loads(file)
            except FileNotFoundError:
                logging.error('The provided file was not found')
        elif isinstance(vals, dict):
            self.metadata=vals
        else:
            logging.error('Not supported configuration\'s input')

    def message_treatment(self, message):
        """
        Main function to handle double way traffic of IoT Service.

        Parameters
        -----
        message: core.Message
            Message object containing the necessary information for its processing.
        """
        try:
            super.validate_message(message)
            super.validate_inputs(message.func_inputs)
        except AssertionError:
            print('Invalid Message Object')
        main = {'client_id': message.client_id}
        cmd = message.message['cmd'].upper()
        func = [o.cmd for o in [WalletFunctions, NodeFunctions, ExtensionFunctions] for f in o if f == cmd]
        params = func(message.func_inputs)
        if isinstance(list, params) or isinstance(tuple, params):
            for p in params:
                main.update(p)
        elif isinstance(dict, params):
            main.update(params)
        else:
            try:
                from_json = json.loads(params)
                main.update(from_json)
            except ValueError:
                print("There was an error returning \
                        your result")
        return main