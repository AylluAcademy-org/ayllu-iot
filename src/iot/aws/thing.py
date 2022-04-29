# General imports
import sys
import subprocess
import asyncio.futures as futures
from uuid import uuid4
import json

from abc import ABC
from typing import Union

from awscrt import io, mqtt, auth  # type: ignore
from awsiot import mqtt_connection_builder  # type: ignore

# Module imports
from src.utils.path_utils import file_exists, get_root_path, validate_path
from src.utils.data_utils import load_configs
from src.utils.path_utils import create_folder
from src.iot.core import Message, Device, Thing

working_dir = get_root_path()

TARGET_FOLDERS = ['cert', 'key', 'root-ca']


class Callbacks(ABC):
    """
    Set of callbacks to be used in connection definitions
    """
    connection: mqtt.Connection

    @property
    def connection(self) -> mqtt.Connection:
        """
        Getter method for abstract class for connection attribute
        """
        return self.connection

    @connection.setter
    def connection(self, new_connection: mqtt.Connection) -> None:
        self.connection = new_connection

    @classmethod
    def on_connection_resumed(self, return_code: mqtt.ConnectReturnCode,
                              session_present: bool, **kwargs) -> None:
        """
        Callback for MQTT Connection
        """
        print(f"Connection resumed. Return Code: {return_code} \
                \n is Session Present: {session_present}")

        if (return_code == mqtt.ConnectReturnCode.ACCEPTED
                and not session_present):
            print("Session connection failed. \
                    Resubscribing to existing topics with new connection...")
            resubscribe_future, _ = self.connection\
                .resubscribe_existing_topics()
            # Cannot synchronously wait for resubscribe result
            # because we're on the connection's event-loop thread,
            # evaluate result with a callback instead.
            resubscribe_future.add_done_callback(self._on_resubscribe_complete)

    def _on_resubscribe_complete(self, resubscribe_future):
        """
        Callback `method for on_conection_resumed` to check wheter
        resubscription was successfull or not
        """
        resubscribe_results = resubscribe_future.result()
        print(f"Resubscribe results: {resubscribe_results}")

        for t, qos in resubscribe_results['topics']:
            if qos is None:
                sys.exit("Server rejected resubscribe to topic: {t}")


class IotCore(Thing, Callbacks):
    """
    Thing object that manages the incoming traffic trough Device objects
    """
    connection: mqtt.Connection
    _metadata: dict
    _topic_queue: dict
    _handler: Device

    def __init__(self, handler_object: Device,
                 config_path: Union[str, dict] = 'config/aws_config.json') \
            -> None:
        """
        Constructor method for Thing object

        Parameters
        ----------
        """
        configs = config_path if config_path != 'config/aws_config.json' \
            else f'{working_dir}/{config_path}'
        self._files_setup(configs)
        self._metadata['client_id'] = "test-" + str(uuid4())
        if issubclass(handler_object, Device):
            super().__init__()
            self.connection = self._create_connection()
            self.topic_queue = {}
            self.handler = handler_object
        else:
            raise TypeError("Provide a valid device handler")

    @property
    def metadata(self) -> dict:
        """
        Getter for metadata attribute
        """
        return self._metadata

    @property
    def topic_queue(self) -> dict:
        return self._topic_queue

    @property
    def handler(self) -> Device:
        return self._handler

    @classmethod
    def get_client_id(self) -> str:
        """
        Function for logging purposes so not to expose metadata attribute
        """
        return self._metadata['client_id']

    @classmethod
    def get_topic(self) -> str:
        """
        Getter function for topic metadata
        """
        # To-do: Implement array for multiple topic initialization
        return self._metadata['topic']

    def _create_connection(self, session_restart: bool = False) \
            -> mqtt.Connection:
        """
        Implementation of mqtt connection method
        """
        event_loop_group = io.EventLoopGroup()
        default_host = io.DefaultHostResolver(event_loop_group)
        client_bootstrap = io.ClientBootstrap(event_loop_group, default_host)
        proxy_options = None
        credentials_provider = auth.AwsCredentialsProvider\
            .new_default_chain(client_bootstrap)
        mqtt_connection = mqtt_connection_builder\
            .websockets_with_default_aws_signing(
                endpoint=self.metadata['endpoint'],
                client_bootstrap=client_bootstrap,
                region=self.metadata['signing_region'],
                credentials_provider=credentials_provider,
                http_proxy_options=proxy_options,
                ca_filepath=self.metadata['root-ca'],
                on_connection_resumed=self.on_connection_resumed,
                client_id=self.metadata['client_id'],
                clean_session=session_restart,
                keep_alive_secs=30)
        return mqtt_connection

    def _files_setup(self, vals: Union[str, dict]):
        self._metadata = load_configs(vals)
        for f in TARGET_FOLDERS:
            create_folder(self.metadata[f])
        self._download_certificates(self.metadata['root-ca'])
        if not all(b is True for b in file_exists([self.metadata['cert'],
                                                   self.metadata['cert']])):
            raise FileExistsError("RSA Keys are not available at the indicated\
                                    path")

    @staticmethod
    def _download_certificates(output_path: str) -> None:
        verified_path = f"{working_dir}/{validate_path(output_path)}"
        if not file_exists(verified_path):
            print("Downloading AWS IoT Root CA certificate from AWS...\n")
            url_ = "https://www.amazontrust.com/repository/AmazonRootCA1.pem"
            subprocess.run(f"curl {url_} > {verified_path}",
                           shell=True, check=True)
        else:
            print("Certificate file already exists\n Skipping step...")

    @classmethod
    def manage_messages(self, msg_topic: str, payload: json):
        """
        Method for managing incoming messages onto Thing object
        """
        data = json.loads(payload.decode('utf-8'))
        if self.metadata['client_id'] == data['client_id']:
            msg = Message(client_id=data['client_id'],
                          payload={k: v for k, v in data.items()
                                   if k != 'client_id'})
            try:
                # Build list depending on the number of messages to be received
                # (Number is set by the seq identifier in the json file)
                if self.topic_queue[msg_topic]:
                    self.topic_queue[msg_topic].append(msg)
                else:
                    self.topic_queue[msg_topic] = [msg]
                print(f"[{msg.timestamp}] \t\
                    Received message from topic: '{msg_topic}' \n \
                    Current queue:  \t {self.topic_queue[msg_topic]}")
                # Waits until queue lenght equals sequence
                assert len(self.topic_queue[msg_topic]) == msg.payload['seq']
                success = self._process_message(self.topic_queue[msg_topic],
                                                msg_topic)
                if success:
                    self.topic_queue[msg_topic] = []
            except AssertionError:
                if not msg.payload['seq']:
                    print(f"Message without seq param, no command executed \
                            {msg}")
                else:
                    print("Continuing with follow message...")
        else:
            raise KeyError("Connection failed due to client missmatch. \
                            Input the correct id or try another client")

    def _process_message(self, input_msgs: list[Message], topic_msg: str) \
            -> bool:
        """
        Private method to process a topic queue
        """
        for individual_msg in input_msgs:
            answer = self.handler.message_treatment(individual_msg)
            output = json.dumps(answer)
            print(f'########################### \n \
                    Publishing message to topic "{topic_msg}": \t{answer} \
                    \n###########################')
            self.connection.publish(topic=topic_msg, payload=output,
                                    qos=mqtt.QoS.AT_LEAST_ONCE)
        return True

    @classmethod
    def start_logging(self, output_path: str = 'stderr') -> None:
        """
        Set logging for thing runtime
        """
        io.init_logging(getattr(io.LogLevel, self.metadata['verbosity']),
                        output_path)

    @classmethod
    def topic_subscription(self) -> futures.Future.result:
        """
        Enable subscription for things service
        """
        future_obj, id = self.connection.subscribe(
            topic=self.metadata['topic'],
            qos=mqtt.QoS.AT_LEAST_ONCE,
            callback=self.manage_messages)
        return future_obj, id
