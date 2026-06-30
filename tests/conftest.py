import os

import pytest

# Set dummy key before any imports that might trigger settings validation
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy-key-for-unit-tests")


@pytest.fixture
def sample_order_id():
    return "NXY-1001"


@pytest.fixture
def sample_delivered_order_id():
    return "NXY-2002"
