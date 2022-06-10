# General Imports
import json
from typing import Any, Union
# Module Imports
from src.iot.core import Device, Message
from src.cardano.base import Wallet, Node, Keys, IotExtensions
from src.utils.data_utils import load_configs, extract_functions


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

    # To-do: Only import if not loaded
    _device_id: str
    _metadata: dict
    _executors: dict  # type: ignore

    def __init__(self, self_id: str, executors_list=[], cardano_configs=None) -> None:
        """
        Constructor for DeviceCardano class.

        Parameters
        ------
        device_id: str
            Unique identifier for the device.
        """
        self._device_id = self_id
        self._metadata = {}
        if executors_list:
            self._executors = self._initialize_classes(executors_list, cardano_configs)
        else:
            self._executors = self._initialize_classes(["Keys", "Wallet",
                                                        "Node", "IotExtensions"], cardano_configs)
        super().__init__()
        print(f"Device Created: {self.device_id}")

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
        self._metadata = load_configs(vals, True)

    def message_treatment(self, message: Message) -> dict:
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
        super().validate_message(message)
        super().validate_inputs(message.payload)
        main = {'message_id': message.message_id}
        cmd = message.payload['cmd'].lower()
        func = [getattr(obj, f) for obj, f_list in self._executors.items() for f in f_list if f == cmd][0]
        if not func:
            raise ValueError("The specified command does not exists")
        try:
            has_args = True if message.payload['args'] else None
        except KeyError:
            has_args = False
        if has_args:
            print(f"Executing function: {func} \nWith parameters: {message.payload['args']}")
            params = func(message.payload['args'])
        else:
            print(f"Executing function: {func}")
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

    def _initialize_classes(self, classes_list: list, set_configs: Union[str, dict]) -> dict:
        """
        Load necessary objects for runtime executions on data threatment
        """
        initialized_objects: dict[Any, list[str]] = {}
        for obj in classes_list:
            if obj == 'Node':
                node = Node(set_configs)
                initialized_objects[node] = extract_functions(node)
            elif obj == 'Wallet':
                wallet = Wallet(set_configs)
                initialized_objects[wallet] = extract_functions(wallet)
            elif obj == 'Keys':
                keys = Keys(set_configs)
                initialized_objects[keys] = extract_functions(keys)
            elif obj == 'IotExtensions':
                iot_extensions = IotExtensions(set_configs)
                initialized_objects[iot_extensions] = extract_functions(iot_extensions)
            else:
                raise KeyError('Specified object is not implemented for this Device')
        return initialized_objects
