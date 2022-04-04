# General imports
import json
# Package imports
from src.utils.path_utils import get_root_path

def load_cardano_configs():
    parent_dir = get_root_path()
    with open(f'{parent_dir}/config/cardano_config.json') as file:
        configs = json.load(file)
    return configs