# General imports
import json

# Package imports
from src.utils.path_utils import get_root_path
from src.utils.data_utils import check_nested_dicts, flatten_dict


def load_cardano_configs():
    parent_dir = get_root_path()
    with open(f'{parent_dir}/config/cardano_config.json') as file:
        configs = json.load(file)
        if check_nested_dicts(configs):
            configs = flatten_dict(configs, False)
    return configs
