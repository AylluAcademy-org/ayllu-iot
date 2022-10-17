from typing import Any
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass()
class Message:
    """
    Class for the data of messages being pass down to devices objects
    """
    # Implement sort_index
    message_id: str
    payload: dict
    timestamp: datetime = datetime.now()


class Device(ABC):
    """
    Class to be implemented for IoT devices handlers depending on it's
    context target of operations

    Attributes
    ----------
    _device_id: str
        Unique identifier for the device.
    _device_type: int
        Identifier for device implementation being use.
    _metadata: dict
        Configuration values necessary for operations.
    """

    _device_id: str
    _device_type: int
    _metadata: dict

    @property
    @abstractmethod
    def device_id(self) -> str:
        """
        Unique identifier for device object
        """

    @property
    @abstractmethod
    def metadata(self) -> dict:
        """
        Information to be used by object configurations or other methods
        """

    @property
    @abstractmethod
    def device_type(self) -> int:
        """
        Information to be used by the Thing to know which worflow logic
        to make use of.
        """

    @abstractmethod
    def message_treatment(self, message: Message):
        """
        Main function that receives the object from the pubsub and
        defines which function to call and execute
        """

    @staticmethod
    def validate_message(input_msg: Message):
        """
        Validate if each inputed message is an object of class Message

        Parameters
        ----------
        message: iot.core.Message
            Message object with enough information for its operation
        """
        if not isinstance(input_msg, Message):
            raise TypeError("The message type is not valid\n")

    @staticmethod
    def validate_inputs(inputs):
        """
        Validate the inputs from a Message being passed down to the
        function call

        Parameters
        ----------
        inputs: dict
            Input arguments for function call
        """
        if not isinstance(inputs, dict):
            raise AssertionError("The body of the message is not a dictionary")


class Thing(ABC):
    """
    Boilerplate for Thing implementation for different platforms.
    """
    _connection: Any
    _metadata: dict
    _topic_queue: dict
    _handler: Device
    _id_cache: list

    @property
    @abstractmethod
    def metadata(self) -> dict:
        """
        Getter for metadata
        """

    @property
    @abstractmethod
    def topic_queue(self) -> dict:
        """
        Getter for topic_queue
        """

    @property
    @abstractmethod
    def handler(self) -> Device:
        """
        Getter for handler
        """

    @abstractmethod
    def _create_connection(self) -> Any:
        """
        Method to stablish connection with platform trough mqtt protocol
        """

    @abstractmethod
    def manage_messages(self, topic: str, payload):
        """
        Core function containing message treatment logic
        """
