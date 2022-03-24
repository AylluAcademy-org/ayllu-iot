# General imports
import json
# Package imports
from src.conftest import load_cardano_configs
from src.utils.path_utils import get_root_path
from src.iot.core import Message
from extended_devices import TestDeviceCardano, basic_math

def create_message(cmd):
    return Message(client_id='1', message=cmd)

def create_device_cardano():
    return TestDeviceCardano(device_id='T')

def dc_metadata_assertions(configs_dict: dict, dc_object: TestDeviceCardano):
    """
    """
    CARDANO_NETWORK_MAGIC = configs_dict['node']['CARDANO_NETWORK_MAGIC']
    CARDANO_CLI_PATH = configs_dict['node']['CARDANO_CLI_PATH']
    CARDANO_NETWORK = configs_dict['node']['CARDANO_NETWORK']
    TRANSACTION_PATH_FILE = configs_dict['node']['transactions']
    KEYS_FILE_PATH = configs_dict['node']['keys_path']
    URL = configs_dict['node']['URL']

    assert dc_object._metadata['CARDANO_NETWORK_MAGIC'] == CARDANO_NETWORK_MAGIC
    assert dc_object._metadata['CARDANO_CLI_PATH'] == CARDANO_CLI_PATH
    assert dc_object._metadata['CARDANO_NETWORK'] == CARDANO_NETWORK
    assert dc_object._metadata['TRANSACTION_PATH_FILE'] == TRANSACTION_PATH_FILE
    assert dc_object._metadata['KEYS_FILE_PATH'] == KEYS_FILE_PATH
    assert dc_object._metadata['URL'] == URL

def test_dc_metadata():
    """
    """
    node_1 = create_device_cardano()
    node_2 = create_device_cardano()

    configs = load_cardano_configs()

    assert node_1._metadata is None
    assert node_2._metadata is None

    node_1.metadata = configs
    node_2.metadata = get_root_path() + 'config/cardano_config.json'

    dc_metadata_assertions(configs, node_1)
    dc_metadata_assertions(configs, node_2)

def test_message_treatment():
    """
    """
    node = create_device_cardano()

    msg_1 = create_message('not_a_dict') # raise AssertionError
    msg_2 = create_message({'cmd': 'not_a_cmd'}) # raise ValueError
    msg_3 = create_message({'cmd': 'basic_math', 'args': \
                            {'return_list': True}})
    msg_4 = create_message({'cmd': 'basic_math', 'args': \
                            json.dumps({'return_list': False})})
    msg_5 = create_message({'cmd': 'basic_dict', 'args': {}})

    try:
        output_1 = node.message_treatment(msg_1)
    except AssertionError:
        pass
    try:
        output_2 = node.message_treatment(msg_2)
    except ValueError:
        pass
    output_3 = node.message_treatment(msg_3)
    output_4 = node.message_treatment(msg_4)
    output_5 = node.message_treatment(msg_5)

    basic_math_result = {'client_id': '1', 'output_0': 4, \
                    'output_1': 4, 'output_2': 4}

    assert output_3 == basic_math_result
    assert output_4 == basic_math_result
    assert output_5 == {'client_id': '1', 'status': 'successful'}