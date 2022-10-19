from typing import Any, Callable, TypeVar
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
import json
from awscrt import mqtt # type: ignore

TypeProcessor = TypeVar("TypeProcessor", bound=Callable[[Any], None])


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
    _id_cache: list[str]
    _message_processor: TypeProcessor

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

    @property
    @abstractmethod
    def message_processor(self) -> TypeProcessor:
        """
        Getter for message_processor
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

class Processor(ABC):
    """
    Abstract class with a set of message processor for different device
    implementations.
    """

    @classmethod
    def device_processor(cls, device_type: int) -> TypeProcessor:
        """
        Getter method for message_processor function.

        Parameters
        ----------
        device_type: int
            The device implementation type identifier

        Returns
        ------
        TypeProcesor
            The set function for processing messages.
        """
        if device_type == 1:
            return cls._executor_processor
        elif device_type == 2:
            return cls._relayer_processor
        else:
            raise TypeError("The provided device type does not exists!\n")

    def _executor_processor(self, msg_topic: str, global_topic: str) -> None:
        """
        Private method that executes the workflow of a subtopic queue.
        Including the publishing back on the channel for the answers.

        Parameters
        ---------
        msg_topic: str
            Sub-topic for this specific queue of message(s).
        global_topic: str
            The channel topic to which the `Thing` should publish to.
        """
        for num, ind_msg in enumerate(self.topic_queue[msg_topic]['incoming']):
            answer = self.handler.message_treatment(ind_msg)
            output = json.dumps(answer)
            print(f'###########################\n \
                    Publishign result for message in sequence #{num}: {answer}\
                    \n###########################')
            if answer == {'msg_id': msg_topic}:
                self.topic_queue[msg_topic]['answers'].extend(
                    [Message(message_id=msg_topic, payload={})])
            else:
                self.topic_queue[msg_topic]['answers'].extend(
                    [Message(message_id=msg_topic, payload=answer)])
            self.connection.publish(topic=global_topic, payload=output,
                                    qos=mqtt.QoS.AT_LEAST_ONCE,
                                    retain=True)

    def _relayer_processor(self) -> None:
        """
        """
        pass
