import json
import pytest

@pytest.fixture(scope=pytest.Package)
def load_cardano_configs():
    with open('../config/cardano_config.json') as file:
        configs = json.loads(file)
    return configs