"""Pytest configuration and shared fixtures.

For most tests, inherit from BaseTestCase instead of using these fixtures directly.
"""

import os

import pytest

# Disable summarization in tests
os.environ["ENABLE_SUMMARIZATION"] = "false"
os.environ["OPENAI_API_KEY"] = ""
os.environ["HUGGINGFACE_API_KEY"] = ""


@pytest.fixture(scope="session", autouse=True)
def configure_test_environment():
    """Configure environment for all tests."""
    # Import here to ensure env vars are set first
    from utils import config

    config.ENABLE_SUMMARIZATION = False
    config.OPEN_AI_KEY = ""
    config.HUGGINGFACE_API_KEY = ""

    yield
