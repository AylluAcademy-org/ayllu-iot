"""
import os
import json
from src.cardano.base import Node

def test_node_init():
    with open('../../../config/cardano_config.json') as file:
        configs = json.loads(file)
        CARDANO_NETWORK_MAGIC = configs['node']['CARDANO_NETWORK_MAGIC']
        CARDANO_CLI_PATH = configs['node']['CARDANO_CLI_PATH']
        CARDANO_NETWORK = configs['node']['CARDANO_NETWORK']
        TRANSACTION_PATH_FILE = configs['node']['transactions']
        KEYS_FILE_PATH = configs['node']['keys_path']
        URL = configs['node']['URL']

    node = Node()

    assert node.CARDANO_NETWORK_MAGIC == CARDANO_NETWORK_MAGIC
    assert node.CARDANO_CLI_PATH == CARDANO_CLI_PATH
    assert node.CARDANO_NETWORK == CARDANO_NETWORK
    assert node.TRANSACTION_PATH_FILE == TRANSACTION_PATH_FILE
    assert node.KEYS_FILE_PATH == KEYS_FILE_PATH
    assert node.URL == URL

    assert './priv' in os.listdir('../../../')
    assert ['wallets', 'transactions'] in os.listdir('../../../.priv')

def test_insert_command():
    pass

def test_id_to_address():
    pass

def test_query_protocol():
    pass

def test_query_tip_exec():
    pass
"""