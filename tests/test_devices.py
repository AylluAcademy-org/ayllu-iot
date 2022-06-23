# General imports
import json
# Package imports
from aylluiot.core import Message
from tests.extended_devices import TestDeviceCardano


def create_message(cmd):
    return Message(message_id='1', payload=cmd)


def create_device_cardano():
    return TestDeviceCardano('T')


def test_dc_metadata():
    """
    """
    node_1 = create_device_cardano()
    node_2 = create_device_cardano()

    assert node_1.metadata == {}
    assert node_2.metadata == {}


def test_message_treatment():
    """
    """
    node = create_device_cardano()

    # msg_1 = create_message('not_a_dict') # raise AssertionError
    # msg_2 = create_message({'cmd': 'not_a_cmd'}) # raise ValueError
    msg_3 = create_message({'cmd': 'basic_math', 'args':
                            {'return_list': True}})
    msg_4 = create_message({'cmd': 'basic_math', 'args':
                            json.dumps({'return_list': False})})
    msg_5 = create_message({'cmd': 'basic_dict', 'args': {}})

    """
    try:
        output_1 = node.message_treatment(msg_1)
    except AssertionError:
        pass
    try:
        output_2 = node.message_treatment(msg_2)
    except ValueError:
        pass
    """
    output_3 = node.message_treatment(msg_3)
    output_4 = node.message_treatment(msg_4)
    output_5 = node.message_treatment(msg_5)

    basic_math_result = {'message_id': '1', 'output_0': 4,
                         'output_1': 4, 'output_2': 4}

    assert output_3 == basic_math_result
    assert output_4 == basic_math_result
    assert output_5 == {'message_id': '1', 'status': 'successful'}
