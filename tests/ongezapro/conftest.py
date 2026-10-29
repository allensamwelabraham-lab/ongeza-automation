import pytest


@pytest.fixture
def app_key():
    return "ongezapro"


def pytest_collection_modifyitems(items):
    for item in items:
        if "/tests/ongezapro/" in str(item.fspath).replace("\\", "/"):
            item.add_marker(pytest.mark.ongezapro)
