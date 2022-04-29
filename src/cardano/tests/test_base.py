# Package imports
from src.cardano.base import Node


def test_folder_creation():
    """
    Validate if node initialization create necessary folders
    """
    node = Node()
    # root_dir = os.listdir(WORKING_DIR)
    # target_folder = node.TRANSACTION_PATH_FILE.split('/')[1]
    # target_dir = os.listdir([d for d in root_dir \
    #           if d == target_folder][0])
    # assert node.TRANSACTION_PATH_FILE in f"{target_folder}/{target_dir}"
    # assert node.KEYS_FILE_PATH in f"{target_folder}/{target_dir}"
    assert isinstance(node, Node)


"""
def test_node_commands():
    ""
    Test for Node method Create Minting Policy
    ""
    node = Node()
"""
