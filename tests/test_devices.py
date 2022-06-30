"""
Suite of tests for 'devices' sub-module.
"""

# General imports
import logging
import pytest
from typing import Callable, Optional
# Package imports
from aylluiot.core import Message
from aylluiot.devices import DeviceExecutors
from tests.extended_devices import TestDEFuncsOne, TestDEFuncsTwo


@pytest.fixture
def make_message() -> Callable:
    """
    Factory fixture to create Messages.

    Returns
    -------
    Callable
        Internal function wrapped for factory.
    """
    def _make_message(cmd: Optional[dict] = {'cmd': None, 'args': []}) \
            -> Message:
        """
        Internal function that builds the message.

        Parameters
        --------
        cmd: dict, default = {'cmd': None, 'args': []}
            The payload of the message.

        Returns
        -------
        Message
            Message object with default `message_id` of '1' and the payload 
            given.
        """
        return Message(message_id='1', payload=cmd)
    return _make_message


@pytest.fixture
def device_executor() -> Callable:
    """
    Factory fixture that returns an instance of the stated object.

    Returns
    -------
    Callable
        Internal function wrapped for factory.
    """
    def create_device_executor(mock_id: Optional[str] = 'Test',
                               mock_executors: Optional[list] = [])\
            -> DeviceExecutors:
        """
        Internal function that instantiates a DeviceExecutors.

        Parameters
        ----------
        mock_id: Optional[str], default = 'Test'
            `device_id` attribute to be used by the instance.
        mock_executors: Optional[list], default = []
            `executors` attributo to be used.

        Returns
        -------
        DeviceExecutors
            Instance of DeviceExecutors with Test executors.
        """
        if not mock_executors:
            mock_executors = [TestDEFuncsOne(), TestDEFuncsTwo()]
        return DeviceExecutors(self_id=mock_id, executors_list=mock_executors)
    return create_device_executor


@pytest.fixture
def mock_configs() -> dict:
    """
    Simple fixture that returns a template `metadata` for Devices 
    implementations.

    Returns
    dict
        Default dict with as key the string 'label' and as value 
        the str 'pytest'.
    """
    return {'label': 'pytest'}


def test_de_constructor(device_executor, mock_configs) -> None:
    """ 
    Test DeviceExecutors constructor.

    Parameters:
    device_executor: pytest.fixture(device_executor)
        Instance to be test against called trough the fixture.
    """
    device = device_executor()
    assert device.device_id == 'Test'


def test_de_metadata(device_executor, mock_configs) -> None:
    """
    Test DeviceExecutors `metadata` attribute getter and setter.

    Parameters
    ----------
    device_executor: pytest.fixture(device_executor)
        Instance to be test against, called trough the fixture.
    """
    device = device_executor()
    assert device.metadata == {}
    device.metadata = mock_configs
    assert device.metadata == mock_configs


def test_message_treatment(device_executor, make_message) -> None:
    """
    Test a diversify set of situations when processing messages.

    Parameters
    ----------
    device_executor: pytest.fixture(device_executor)
        Instance to be test against, called trough the fixture.
    make_message: pytest.fixture(make_message)
        Factory fixture to create the messages for testing.
    """
    device = device_executor()

    msg_1 = make_message('not_a_dict')
    msg_2 = make_message({'cmd': 'not_a_cmd'})
    msg_3 = make_message({'cmd': 'basic_math', 'args':
                          {'inputed': 3, 'expected': 2}})
    msg_4 = make_message({'cmd': 'basic_math', 'args':
                          {'inputed': 'yes', 'expected': 'yes'}})
    msg_5 = make_message({'cmd': 'basic_dict', 'args': {}})

    output_3 = device.message_treatment(msg_3)
    output_4 = device.message_treatment(msg_4)
    output_5 = device.message_treatment(msg_5)

    try:
        _ = device.message_treatment(msg_1)
    except AssertionError:
        logging.info('Expected Error checked.')
    try:
        _ = device.message_treatment(msg_2)
    except ValueError:
        logging.info('Expected Error checked.')
    assert output_3 == {'message_id': '1', 'output': None}
    assert output_4 == {'message_id': '1', 'output_0': 4, 'output_1': 4,
                        'output_2': 4}
    assert output_5 == {'message_id': '1', 'status': 'successful'}
