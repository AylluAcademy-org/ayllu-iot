from typing import Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass()
class Message:
    """
    Class for the data of messages being pass down to devices objects
    """

    # Implement sort_index
    client_id: str
    message: dict
    timestamp: datetime = datetime.now()


class Device(ABC):
    """
    Class to be implemented for IoT things devices depending on it's
    context target of operations

    Attributes
    ----------
    _device_id: str
        Unique identifier for the device.
    _metadata: dict
        Configuration values necessary for operations.
    """

    _device_id: str
    _metadata: dict

    @property
    @abstractmethod
    def device_id(self) -> str:
        """
        Unique identifier for device object
        """
        pass

    @property
    @abstractmethod
    def metadata(self):
        """
        Information to be used by object configurations or other methods
        """
        pass

    @classmethod
    @abstractmethod
    def message_treatment(self,
                          client_id):
        """
        Main function that receives the object from the pubsub and
        defines which function to call and execute
        """
        pass

    @staticmethod
    def validate_message(message: Message) \
            -> Optional[AssertionError]:
        """
        Validate if each inputed message is an object of class Message

        Parameters
        ----------
        message: iot.core.Message
            Message object with enough information for its operation

        Returns
        ------
        result: Optional[AssertionError]
            Indicator wether the message is valid or not
        """
        if isinstance(message, Message):
            return None
        else:
            return AssertionError("The message is not valid")

    @staticmethod
    def validate_inputs(inputs) -> Optional[AssertionError]:
        """
        Validate the inputs from a Message being passed down to the
        function call

        Parameters
        ----------
        inputs: dict
            Input arguments for function call

        Returns
        -------
        result: Optional[AssertionError]
            Indicator wether the inputs are valid or no
        """
        if isinstance(inputs, dict):
            return None
        else:
            return AssertionError("The body of the message is not a \
                                dictionary")
