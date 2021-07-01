# Copyright 2020–2021 Cirq on IQM developers
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Mocks server calls for testing
"""

import json
import os
from uuid import UUID

import pytest
import requests
from mockito import mock, unstub, when
from requests import Response

existing_run = UUID('3c3fcda3-e860-46bf-92a4-bcc59fa76ce9')
missing_run = UUID('059e4186-50a3-4e6c-ba1f-37fe6afbdfc2')


@pytest.fixture()
def base_url():
    return 'https://example.com'


@pytest.fixture(scope='function')
def mock_server(base_url):
    """
    Runs mocking separately for each test
    """
    generate_server_stubs(base_url)
    yield  # running test function
    unstub()


@pytest.fixture
def settings_dict():
    """
    Reads and parses settings file into a dictionary
    """
    settings_path = os.path.dirname(os.path.realpath(__file__)) + '/settings.json'
    with open(settings_path, 'r') as f:
        return json.loads(f.read())


def generate_server_stubs(base_url):
    """
    Mocking some of the calls to the server by mocking 'requests'
    """
    success_submit_response = mock({'status_code': 201, 'text': json.dumps({'id': str(existing_run)})})
    when(requests).post(f'{base_url}/circuit/run', ...).thenReturn(success_submit_response)

    running_response = mock({'status_code': 200, 'text': json.dumps({'status': 'pending'})})
    success_get_response = mock({'status_code': 200, 'text': json.dumps(
        {'status': 'ready', 'measurements': {'result': [[1, 0, 1, 1], [1, 0, 0, 1], [1, 0, 1, 1], [1, 0, 1, 1]]}})})

    # run was not created response
    no_run_response = Response()
    no_run_response.status_code = 404
    no_run_response.reason = 'Run not found'

    when(requests).get(f'{base_url}/circuit/run/{existing_run}', ...). \
        thenReturn(running_response).thenReturn(success_get_response)
    when(requests).get(f'{base_url}/circuit/run/{missing_run}', ...).thenReturn(no_run_response)
