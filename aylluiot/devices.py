"""
Set of implementations for Device
"""

# General Imports
import json
from typing import Union, Generic, TypeVar
from pydantic import BaseModel
# Module Imports
from aylluiot.core import Device, Message
from aylluiot.utils.data import load_configs
from aylluiot.utils.devices import extract_functions


TypeDevice = TypeVar('TypeDevice', bound=Device)


class DeviceExecutors(Device, Generic[TypeDevice]):
    """
    Class implementation for IoT device interacting trough object instances.
    It specializes in processing topics queues and publishing responses.

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

    _device_id: str
    _metadata: dict
    _executors: dict

    def __init__(self, self_id: str, executors_list: list) -> None:
        """
        Constructor for DeviceCardano class.

        Parameters
        ------
        self_id: str
            Unique identifier for the device.
        executors_list: list
            Instance of classes to be utilized as executors
        """
        self._device_id = self_id
        self._metadata = {}
        self._device_type = 1
        self._executors = self._initialize_classes(executors_list)
        super().__init__()
        print(f"Device Created: {self.device_id}")

    @property
    def device_id(self) -> str:
        """
        Get the current id from the device.
        """
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
        vals: Union[str, dict]
            The parameters to be set. If str it should be an json
            file to be read. Else, an already loaded python
            dictionary.
        """
        self._metadata = load_configs(vals, True)

    @property
    def device_type(self) -> int:
        """
        Get the device type identifier.
        """
        return self._device_type

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
        _func = [getattr(obj, f) for obj, f_list in self._executors.items()
                 for f in f_list if f == cmd]
        if not _func:
            raise ValueError("The specified command does not exists")
        else:
            func = _func[0]
        try:
            has_args = True if message.payload['args'] else None
        except KeyError:
            has_args = False
        if has_args:
            print(
                f"Executing function: {func} \nWith parameters: \
                    {message.payload['args']}")
            params = func(message.payload['args'])
        else:
            print(f"Executing function: {func}")
            params = func()
        if isinstance(params, list) or isinstance(params, tuple):
            p = {f"output_{v}": params[v] for v in range(len(params))}
            main.update(p)
        elif isinstance(params, dict):
            main.update(params)
        elif (isinstance(params, str)) or (isinstance(params, bytes)):
            try:
                from_json = json.loads(params)
                main.update(from_json)
            except ValueError:
                print("There was an error returning your result")
        else:
            main.update({'output': params})
        return main

    def _initialize_classes(self, instances: list) -> dict:
        """
        Load necessary objects for runtime executions on data threatment,
        """
        if instances:
            return {ins: extract_functions(ins) for ins in instances}
        else:
            raise TypeError('The given list is empty.')


class DeviceRelayer(Device, Generic[TypeDevice]):
    """
    Class implemention for an IoT Message Relayer. It specializes in validating
    and formatting messages gotten from other instances to be processed by
    another topic `DeviceExecutor` instance.
    
    Attributes
    ----------
    _device_id: str
    """

    _device_id: str
    _metadata: dict
    _validators: list

    def __init__(self, self_id: str, validators_list: list) -> None:
        """
        Constructor for DeviceRelayer class.

        Parameters
        ----------
        self_id: str
            Unique identifier for the device
        """
        self._device_id = self_id
        self._metadata = {}
        self._device_type = 2
        self._validators = self._initialize_validators(validators_list)
        super().__init__()
        print(f"Device Created: {self.device_id}")

    @property
    def devide_id(self) -> str:
        """
        Get the current id from the device.
        """
        return self._device_id

    @property
    def metadata(self) -> dict:
        """
        Get the current mentadata.
        """
        return self._metadata

    @metadata.setter
    def metadata(self, vals: Union[str, dict]) -> None:
        """
        Set a valid metadata paremeter.

        Parameters
        ----------
        vals: Union[str, dict]
            The parameters to be set. If str it should be an json
            file to be read. Else, an already loaded python
            dictionary.
        """
        self._metadata = load_configs(vals, True)
    
    @property
    def device_type(self) -> int:
        """
        Get the device type identifier.
        """
        return self._device_type

    def message_treatment(self, message: Message) -> dict:
        """
        Main function to handle double way traffic of IoT Service.

        Parameters
        --------
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
        

    def _initialize_validators(self, instances: list) -> list:
        """
        Load necessary objects for runtime executions on data threatment.
        """

        output: list = []

        for i in instances:
            if issubclass(i, BaseModel):
                output.append(i)
            else:
                raise TypeError("The given object is not a Pydantic Model!")
        return output
