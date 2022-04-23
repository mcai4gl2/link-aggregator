import os
import pytest


TEST_FILE_DIR = os.path.abspath(os.path.dirname(__file__))
TEST_FILE_DIR = os.path.join(TEST_FILE_DIR, 'files')


@pytest.fixture
def test_mail_content():
    with open(os.path.join(TEST_FILE_DIR, 'test-mail.txt'), 'r') as file:
        return file.read()
