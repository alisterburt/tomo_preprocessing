import pytest
from pathlib import Path


@pytest.fixture
def project_directory():
    return Path(__file__).parent.parent


@pytest.fixture
def test_data_directory():
    return Path(__file__).parent.parent / 'test_data'
