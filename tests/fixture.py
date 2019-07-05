import pytest
from utils import Config


@pytest.fixture
def config():
    config = Config()
    config.obtain_secret('access_key_id')
    config.obtain_secret('access_key_secret')
    return config
