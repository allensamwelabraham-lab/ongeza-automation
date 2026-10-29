import pytest


@pytest.fixture
def app_key():
    return "ongeza"


def pytest_collection_modifyitems(items):
    for item in items:
        if "/tests/ongeza/" in str(item.fspath).replace("\\", "/"):
            item.add_marker(pytest.mark.ongeza)
