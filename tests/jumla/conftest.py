import pytest


@pytest.fixture
def app_key():
    return "jumla"


def pytest_collection_modifyitems(items):
    for item in items:
        if "/tests/jumla/" in str(item.fspath).replace("\\", "/"):
            item.add_marker(pytest.mark.jumla)
