# General imports
import sys
import os
import subprocess
from uuid import uuid4
from datetime import datetime
import json

from abc import ABC
from typing import Union, TypeVar, Generic

from dotenv import load_dotenv  # type: ignore
from awscrt import io, mqtt, auth  # type: ignore
from awsiot import mqtt_connection_builder  # type: ignore

# Module imports
from aylluiot.utils.path_utils import file_exists, validate_path, get_root_path
from aylluiot.utils.data_utils import load_configs
from aylluiot.core import Message, Device, Thing

WORKING_DIR = get_root_path()

TARGET_FOLDERS = ['cert', 'key', 'root-ca']
TARGET_AWS = ['AWS_KEY_ID', 'AWS_SECRET_KEY', 'AWS_REGION']
AWS_DEFAULTS = ['aws_access_key_id', 'aws_secret_access_key', 'region']

TypeDevice = TypeVar('TypeDevice', bound=Device)

MESSAGE_TEMPLATE = {
    'client_id': 'Here goes the device id',
    'seq': 'Number of messages [an integer higher than zero]',
    'cmd': '[Here goes a valid function name for this thing device, ...]',
    'args (optional)': '[{Only if: the function requires it}, ...]'}
WARNING_TEMPLATE = f"Please follow the guidelines: {MESSAGE_TEMPLATE}\n\
            Note that if any of your commands has an argument you \
            have to fill with `null` the rest of the list to make it \
            clear which correspond to which!\nTry sending a new request...\n"


class Callbacks(ABC):
    """
    Set of callbacks to be used in connection definitions
    """
    _connection: mqtt.Connection

    @property
    def connection(self) -> mqtt.Connection:
        """
        Getter method for abstract class for connection attribute
        """
        return self._connection

    @connection.setter
    def connection(self, new_connection: mqtt.Connection) -> None:
        self._connection = new_connection

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
            resubscribe_future, _ = self._connection\
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


class IotCore(Thing, Callbacks, Generic[TypeDevice]):
    """
    Thing object that manages the incoming traffic trough Device objects
    """
    _connection: mqtt.Connection
    _metadata: dict
    _handler: TypeDevice
    _topic_queue: dict
    # _id_cache: list[str]

    def __init__(self,
                 handler_object,
                 config_path: Union[str,
                                    dict] = 'config/aws_config.json'):
        """
        Constructor method for Thing object

        Parameters
        ----------
        """
        load_dotenv()
        configs = config_path \
            if config_path != "config/aws_config.json" else \
            f'{WORKING_DIR}/{config_path}'
        self._files_setup(configs)
        if issubclass(handler_object, Device):
            super().__init__()
            self._handler = handler_object("thing-" + str(uuid4()))
            # Pending adding metadata for handler_object
            self.topic_queue = {}
            self._id_cache = []
            self.connection = self._create_connection()
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

    @topic_queue.setter
    def topic_queue(self, new_queue):
        self._topic_queue = new_queue

    @property
    def handler(self) -> TypeDevice:
        return self._handler

    @property
    def id_cache(self):
        return self._id_cache

    @id_cache.setter
    def id_cache(self, new_id: Union[str, list[str]]):
        if isinstance(new_id, str):
            self._id_cache.extend([new_id])
        elif isinstance(new_id, list):
            self._id_cache.extend(new_id)
        else:
            raise TypeError("Provide a valid new_id type")

    @id_cache.deleter
    def id_cache(self, num: int = -1):
        if (self.id_cache) and (num == -1):
            self._id_cache.clear()
        elif (num >= 0) and (len(self.id_cache) >= num):
            del self._id_cache[0: num]
        else:
            raise KeyError("Provide a valid number to delete")

    def _get_client_id(self) -> str:
        """
        Function for logging purposes so not to expose metadata attribute
        """
        return self.handler.device_id

    def _get_topic(self) -> str:
        """create_folder
        Getter function for topic metadata
        """
        # To-do: Implement array for multiple topic initialization
        return self.metadata['AWS_TOPIC']

    def _create_connection(self) -> mqtt.Connection:
        """
        Implementation of mqtt connection method
        """
        event_loop_group = io.EventLoopGroup()
        default_host = io.DefaultHostResolver(event_loop_group)
        client_bootstrap = io.ClientBootstrap(event_loop_group, default_host)
        proxy_options = None
        credentials_provider = auth.AwsCredentialsProvider\
            .new_static(access_key_id=self.metadata['AWS_KEY_ID'],
                        secret_access_key=self.metadata['AWS_SECRET_KEY'])
        mqtt_connection = mqtt_connection_builder\
            .websockets_with_default_aws_signing(
                endpoint=self.metadata['AWS_IOT_ENDPOINT'],
                client_bootstrap=client_bootstrap,
                region=self.metadata['AWS_REGION'],
                credentials_provider=credentials_provider,
                http_proxy_options=proxy_options,
                ca_filepath=validate_path(self.metadata['root-ca'], True),
                on_connection_resumed=self.on_connection_resumed,
                client_id=self._get_client_id(),
                clean_session=True, keep_alive_secs=30)
        return mqtt_connection

    def _files_setup(self, vals: Union[str, dict]):
        self._metadata = load_configs(vals, False)
        for f in TARGET_FOLDERS:
            validate_path(self.metadata[f], True, True)
        self._download_certificates(validate_path(self.metadata['root-ca'],
                                    True))
        if not all([file_exists(p)
                   for p in [self.metadata['cert'], self.metadata['key']]]):
            raise FileExistsError("RSA Keys are not available at the indicated\
                                    path")
        env_vars = ['AWS_IOT_ENDPOINT', 'AWS_IOT_PORT', 'AWS_IOT_UID',
                    'AWS_REGION', 'AWS_KEY_ID', 'AWS_SECRET_KEY', 'AWS_TOPIC']
        for var in env_vars:
            try:
                if os.environ[var] != '':
                    self._metadata[var] = os.environ[var]
            except KeyError:
                continue
        self._validate_aws_credentials()

    def _validate_aws_credentials(self):
        missing = []
        for num, val in enumerate(TARGET_AWS):
            if val not in self._metadata.keys():
                try:
                    self._metadata[val] = os.environ[AWS_DEFAULTS[num]]
                except KeyError:
                    missing.append(val)
                    continue
        if any([True for t in TARGET_AWS[:2] if t in missing]):
            try:
                f = open(f"{os.environ['HOME']}/.aws/credentials")
                f.close()
            except FileNotFoundError:
                raise FileNotFoundError('Missing IAM Configs')
        elif TARGET_AWS[-1] in missing:
            try:
                f = open(f"{os.environ['HOME']}/.aws/config")
                f.close()
            except FileNotFoundError:
                raise FileNotFoundError('IoT Region is not set')

    @staticmethod
    def _download_certificates(output_path: str) -> None:
        if not file_exists(output_path, True):
            print("Downloading AWS IoT Root CA certificate from AWS...\n")
            url_ = "https://www.amazontrust.com/repository/AmazonRootCA1.pem"
            subprocess.run(f"curl {url_} > {output_path}",
                           shell=True, check=True)
        else:
            print("Certificate file already exists\t Skipping step...")

    def manage_messages(self, topic: str, payload: bytes) -> None:
        """
        Method for managing incoming messages onto Thing object
        """
        data = json.loads(payload.decode('utf-8'))
        if not self._filter_queue(data):
            if 'client_id' in data.keys():
                try:
                    assert self._get_client_id() == data['client_id']
                    queued_topic = f"{topic}-{str(uuid4())}"
                    msg = Message(message_id=queued_topic,
                                  payload={k: v for k, v in data.items()
                                           if k != 'client_id'})
                    msg_queue = self._unpack_payload(msg)
                    if msg_queue:
                        print(
                            f"[{msg.timestamp}] Received message from topic: \
                                '{queued_topic}'")
                        self.topic_queue[queued_topic] = {
                            'incoming': [], 'answers': [],
                            'start_time': msg.timestamp}
                        self.topic_queue[queued_topic]['incoming'].extend(
                            msg_queue)
                        print(
                            f"[{datetime.now()}] Initializing sequence \
                            execution from: {queued_topic}\n\
                            Using the following queue: \
                            {self.topic_queue[queued_topic]['incoming']}\n")
                        self._process_message(queued_topic, topic)
                        self.id_cache = queued_topic
                        self.topic_queue.pop(queued_topic)
                        print(
                            f"Done with execution for {queued_topic}. \
                                Continuing with the following message...\n")
                except AssertionError:
                    print(
                        'Client missmatch. Please input the correct client \
                            id\nContinuing with the following message...\n')
            else:
                raise KeyError(f"Missing `client_id`. {WARNING_TEMPLATE}")
        else:
            print("Ommiting message as it's part of a sequence in \
                execution...\n")

    def _process_message(self, msg_topic: str, global_topic: str):
        """
        Private method to process a topic queue
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
                                    qos=mqtt.QoS.AT_LEAST_ONCE)

    def _unpack_payload(self, input_msg: Message) -> list[Message]:
        """
        Preprocessing for upcoming messages. Build a list depending on the
        number of messages to be processed.
        This number is set by the `seq` identifier in the json payload.
        """
        output_queue = []
        main_id = input_msg.message_id
        validation_result = self._validate_payload(input_msg)
        new_payloads = self._repackage_payload(input_msg.payload)
        if validation_result and new_payloads != [{}]:
            if input_msg.payload['seq'] > 1:
                for i in range(0, input_msg.payload['seq']):
                    output_queue.append(
                        Message(
                            message_id=main_id,
                            payload=new_payloads[i]))
            elif input_msg.payload['seq'] == 1:
                output_queue.append(
                    Message(
                        message_id=main_id,
                        payload=new_payloads[0]))
        return output_queue

    def _validate_payload(self, input_payload: Message) -> bool:
        """
        Checks for required parameters in message payload
        """
        payload_keys = input_payload.payload.keys()
        if 'seq' not in payload_keys:
            raise TypeError(
                f'Invalid message. `seq` is not included in the Message. \
                    {WARNING_TEMPLATE}')
        elif input_payload.payload['seq'] < 1:
            raise TypeError(
                f'Invalide message. `seq` cannot be a negative value nor zero.\
                    {WARNING_TEMPLATE}')
        elif ('cmd' not in payload_keys):
            raise TypeError(
                f'Parameter `cmd` was not found. {WARNING_TEMPLATE}')
        elif ('cmd' in payload_keys) and \
                not isinstance(input_payload.payload['cmd'], list):
            raise TypeError(
                f'Invalid message. `cmd` is not as expected. \
                    {WARNING_TEMPLATE}')
        try:
            assert len(
                input_payload.payload['cmd']) == (
                input_payload.payload['seq'])
        except AssertionError:
            print('The sequence given does not match with the number of \
                commands\n')
        return True

    def _repackage_payload(self, input_payload: dict) -> list[dict]:
        output_payloads: list[dict] = [{}]
        try:
            assert len(input_payload['cmd']) == len(input_payload['args'])
            if len(input_payload['cmd']) > 1:
                output_payloads = [
                    {'cmd': input_payload['cmd'][i],
                     'args': input_payload['args'][i]}
                    for i in range(0, len(input_payload['cmd']))]
            else:
                output_payloads = [
                    {'cmd': input_payload['cmd'][0],
                        'args': input_payload['args'][0]}]
        except KeyError:
            if len(input_payload['cmd']) > 1:
                output_payloads = [
                    {'cmd': input_payload['cmd'][i], 'args': None}
                    for i in range(0, len(input_payload['cmd']))]
            else:
                output_payloads = [
                    {'cmd': input_payload['cmd'][0], 'args': None}]
        except AssertionError:
            print(
                f'The number of `cmd` does not correspond with the number \
                    of `args`. {WARNING_TEMPLATE}')
        except TypeError:
            print(
                f"The format of `args` is not as expected. {WARNING_TEMPLATE}")
        return output_payloads

    def _filter_queue(self, check_msg: dict) -> bool:
        """
        Check for upcoming messages and filter self publish answers
        """
        try:
            in_queue = check_msg['message_id'] in self.topic_queue.keys()
        except KeyError:
            in_queue = False
        return in_queue

    def start_logging(self, output_path: str = 'stderr') -> None:
        """
        Set logging for thing runtime
        """
        no_logs = self.metadata['verbosity']['Info']
        io.init_logging(getattr(io.LogLevel, no_logs), output_path)

    def topic_subscription(self) -> tuple[dict, int]:
        """
        Enable subscription for things service
        """
        future_obj, id = self.connection.subscribe(
            topic=self.metadata['AWS_TOPIC'],
            qos=mqtt.QoS.AT_LEAST_ONCE,
            callback=self.manage_messages)
        return future_obj, id
