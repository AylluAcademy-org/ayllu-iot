"""
Thing object implementations that enable interactiong with AWS services.
"""

# General imports
import sys
import os
import subprocess
from concurrent.futures import Future
from uuid import uuid4
from datetime import datetime
import json
import logging

from abc import ABC
from typing import Generic

from dotenv import load_dotenv  # type: ignore
from awscrt import io, mqtt, auth  # type: ignore
from awsiot import mqtt_connection_builder  # type: ignore

# Module imports
from aylluiot.utils.path_utils import file_exists, validate_path
from aylluiot.utils.data_utils import load_configs
from aylluiot.core import Message, Device, Thing
from aylluiot.devices import TypeDevice

TARGET_FOLDERS = ['cert', 'key', 'root-ca']
TARGET_AWS = ['AWS_KEY_ID', 'AWS_SECRET_KEY', 'AWS_REGION']
AWS_DEFAULTS = ['aws_access_key_id', 'aws_secret_access_key', 'region']

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
    Abstract class with a set of callbacks to be used by the comms methods in
    a Thing implementation that relies on IoT Core.

    Attributes
    ----------
    connection: mqtt.Connection
        MQTT client connection object from AWS SDK.
    """
    _connection: mqtt.Connection

    @property
    def connection(self) -> mqtt.Connection:
        """
        Getter method for connection attribute.

        Returns
        -------
        mqtt.Connection
            MQTT client connection object from AWS SDK.
        """
        return self._connection

    @connection.setter
    def connection(self, new_connection: mqtt.Connection) -> None:
        """
        Setter method for connection attribute.

        Parameters
        ---------
        new_connection: mqtt.Connection
            Replacement MQTT client connection object.
        """
        self._connection = new_connection

    def on_connection_resumed(self, return_code: mqtt.ConnectReturnCode,
                              session_present: bool, **kwargs) -> None:
        """
        Callback for MQTT Connection invoked whenever the MQTT connection is
        automatically resumed.

        Parameters
        ---------
        return_code: mqtt.ConnectReturnCode
            Code status from AWSCRT MQTT that indicates connection result.
        session_present: bool
            True if resuming existing session. False if new session.
        """
        print(f"Connection resumed. Return Code: {return_code} \
                \n is Session Present: {session_present}")

        if (return_code == mqtt.ConnectReturnCode.ACCEPTED
                and not session_present):
            print("Session connection failed. \
                    Resubscribing to existing topics with new connection...")
            resubscribe_future, _ = self._connection\
                .resubscribe_existing_topics()
            resubscribe_future.add_done_callback(self._on_resubscribe_complete)

    def _on_resubscribe_complete(self, resubscribe_future: Future) -> None:
        """
        Callback method for `on_conection_resumed` to check wheter
        resubscription was successfull or not.

        Parameters
        ---------
        resubscribe_future: Future
            Return object from calling `resubscribe_existing_topics` on the
            MQTT Client Connection.
        """
        resubscribe_results = resubscribe_future.result()
        print(f"Resubscribe results: {resubscribe_results}")

        for t, qos in resubscribe_results['topics']:
            if qos is None:
                sys.exit("Server rejected resubscribe to topic: {t}")
            else:
                logging.info(f"Resubscribe to topic: {t}")


class IotCore(Thing, Callbacks, Generic[TypeDevice]):
    """
    Thing object that manages the incoming traffic trough Device objects

    Attributes
    ----------
    metadata: dict
        Set-up of configurations set to object trough config file or dict.
    topic_queue: dict
        Sub-topics at runtime. Contain input messages and answers up to current
        status of each sub-topic.

    """
    _connection: mqtt.Connection
    _metadata: dict
    _handler: TypeDevice
    _topic_queue: dict
    _id_cache: list[str]

    def __init__(self, handler_object, config_path: str):
        """
        Constructor method for Thing object

        Parameters
        ----------
        handler_object: TypeDevice
            Implementation of Device object to be used as handler.
        config_path: str
            Configuration path for AWS variables.
        """
        self._files_setup(config_path)
        if issubclass(type(handler_object), Device):
            super().__init__()
            self._handler = handler_object
            # Pending adding metadata for handler_object
            self.topic_queue = {}
            self._id_cache = []
            self.connection = self._create_connection()
        else:
            raise TypeError("Provide a valid device handler")

    @property
    def metadata(self) -> dict:
        """
        Getter method for metadata attribute.

        Returns
        ------
        dict
            Object metadata dict.
        """
        return self._metadata

    @property
    def topic_queue(self) -> dict:
        """
        Getter method for topic_queue attribute.

        Returns
        -------
        dict
            Topic Queue dict.
        """
        return self._topic_queue

    @topic_queue.setter
    def topic_queue(self, new_queue: dict) -> None:
        """
        Setter method for topic_queue attribute.

        Parameters
        ---------
        new_queue: dict
            The new dictionary to be used as queue.
        """
        self._topic_queue = new_queue

    @property
    def handler(self) -> TypeDevice:
        """
        Getter method for handler attribute.

        Returns
        -------
        TypeDevice
            Handler instance in used.
        """
        return self._handler

    @property
    def id_cache(self) -> list[str]:
        """
        Getter method for id_cache attribute.

        Returns
        -------
        dict
            Current list of id_cache of subtopics names.
        """
        return self._id_cache

    @id_cache.setter
    def id_cache(self, new_id: list[str]) -> None:
        """
        Setter method for id_cache attribute. It doesn't replace the attribute
        but instead append or extend the current list to avoid unintentional
        modifications.

        Parameters
        ----------
        new_id: Union[str, list[str]]
            Value to be added at the end of current list.
        """
        if isinstance(new_id, list):
            self._id_cache.extend(new_id)
        else:
            raise TypeError("Provide a valid new_id type")

    @id_cache.deleter
    def id_cache(self, num: int = -1) -> None:
        """
        Deleter method for id_cache attribute. It clears the full list by
        default, but it can be specified only to clear `num` of items.

        Parameters
        ----------
        num: int, defeault = -1
            The number of items to delete from oldest to most recent.
        """
        if (self.id_cache) and (num == -1):
            self._id_cache.clear()
        elif (num >= 0) and (len(self.id_cache) >= num):
            del self._id_cache[0: num]
        else:
            raise KeyError("Provide a valid number to delete")

    def _get_client_id(self) -> str:
        """
        Function for accessing 'device_id' on `handler` metadata.

        Returns
        -------
        str
            The name of the `device_id` from the handler attribute.
        """
        return self.handler.device_id

    def _get_topic(self) -> str:
        """
        Function to access Thing 'topic' in `metadata` attribute.

        Returns
        -------
        str
            Name of the topic that the object will subscribe to.
        """
        return self.metadata['AWS_TOPIC']

    def _create_connection(self) -> mqtt.Connection:
        """
        Implementation of mqtt connection method

        Returns
        ------
        mqtt.Connection
            MQTT Client Connection object from AWS CRT SDK.
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
                ca_filepath=validate_path(self.metadata['root-ca'],
                                          self.metadata['root'], True),
                on_connection_resumed=self.on_connection_resumed,
                client_id=self._get_client_id(),
                clean_session=True, keep_alive_secs=30)
        return mqtt_connection

    def _files_setup(self, vals: str) -> None:
        """
        Private helper function to validate that all the necessary files for
        authentication of AWS are available.

        Parameters
        ----------
        vals: str
            The set of configuration or file location that describes the paths
            for Certificate and Keys of AWS IoT Core.
        """
        self._metadata = load_configs(vals, False)
        load_dotenv(f"{self.metadata['root']}/.env")
        for f in TARGET_FOLDERS:
            validate_path(self.metadata[f], self.metadata['root'], True)
        self._download_certificates(validate_path(self.metadata['root-ca'],
                                    self.metadata['root'], True))
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

    def _validate_aws_credentials(self) -> None:
        """
        Private helper function to search the enviroment variables needed
        for the interaction with AWS services.
        """
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
        """
        Private helper function to download public certificates from AWS.

        Parameters
        ----------
        output_path: str
            The location where to save the download files.
        """
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

        Parameters
        ---------
        topic: str
            The topic which the upcoming messaged should be tagged with.
        payload: bytes
            The incoming payload that will make the Message data.
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
                        self.id_cache = [queued_topic]
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

    def _process_message(self, msg_topic: str, global_topic: str) -> None:
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
                                    qos=mqtt.QoS.AT_LEAST_ONCE)

    def _unpack_payload(self, input_msg: Message) -> list[Message]:
        """
        Internal preprocessing function for upcoming messages. Build a list
        depending on the number of messages to be processed.
        This number is set by the `seq` identifier in the json payload.

        Parameters
        ---------
        input_msg: Message
            Original payload turned as a Message object from the message
            manager function.

        Returns
        -------
        list[Message]
            List of splitted Messages based on the number of commands indicated
            at the payload.
        """
        output_queue = []
        main_id = input_msg.message_id
        validation_result = self._validate_payload(input_msg)
        new_payloads = self._repackage_payload(input_msg.payload)
        if validation_result and new_payloads != [{}]:
            if input_msg.payload['seq'] > 1:
                for i in range(0, input_msg.payload['seq']):
                    output_queue.append(Message(message_id=main_id,
                                                payload=new_payloads[i]))
            elif input_msg.payload['seq'] == 1:
                output_queue.append(Message(message_id=main_id,
                                            payload=new_payloads[0]))
        else:
            raise SyntaxError(f'There was an error figuring out the sequences\
                of `cmd` and `args` from the Messages given.\
                {WARNING_TEMPLATE}')
        return output_queue

    def _validate_payload(self, input_payload: Message) -> bool:
        """
        Internal helper function that checks for required parameters in
        a Message `payload` parameter.

        Parameters
        ----------
        input_payload: Message
            Input Message to be check.

        Returns
        -------
        bool
            It must return True, which means the Message is good to go,
            else raise a specific Exception.
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
        """
        Internal helper function that rebuild a list of Messages with multiple
        `payload` parameters for each.

        Parameters
        ----------
        input_payload: dict
            Dictionary of `cmd` and `args` of multiple Messages.

        Returns
        -------
        output_payloads: list[dict]
            List of dictionaries for each individual message with their
            respective `cmd` and `args`.
        """
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
        Internal helper fucntion that checks for upcoming messages and filters
        self publish answers

        Parameters
        ----------
        check_msg: dict
            Input payload that is recieved by the message manager function.

        Returns
        -------
        in_queue: bool
            Either True or False depending if the message is in queue or not.
        """
        try:
            in_queue = check_msg['message_id'] in self.topic_queue.keys()
        except KeyError:
            in_queue = False
        return in_queue

    def start_logging(self, output_path: str = 'stderr') -> None:
        """
        Set logging for Thing runtime at the connection level using AWSCRT SDK.

        Parameters
        ----------
        output_path: str
            Where to save the logging data.
        """
        no_logs = self.metadata['verbosity']['Info']
        io.init_logging(getattr(io.LogLevel, no_logs), output_path)

    def topic_subscription(self) -> Future:
        """
        Execute first time subscription for Thing connection object.

        Returns
        ------
        future_obj: Future
            The Future resulting of a 'SUBACK' received from the IoT server.
        """
        future_obj, _ = self.connection.subscribe(
            topic=self.metadata['AWS_TOPIC'],
            qos=mqtt.QoS.AT_LEAST_ONCE,
            callback=self.manage_messages)
        return future_obj
