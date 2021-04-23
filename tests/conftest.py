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
Mocks backend calls for testing
"""

import json
from uuid import UUID
import pytest
import requests
from mockito import unstub, when, mock
from requests import Response

BASE_URL = 'https://example.com'

existing_run = UUID('3c3fcda3-e860-46bf-92a4-bcc59fa76ce9')
missing_run = UUID('059e4186-50a3-4e6c-ba1f-37fe6afbdfc2')

@pytest.fixture(scope='function')
def mock_backend():
    """
    Runs mocking separately for each test
    """
    generate_backend_stubs()
    yield  # running test function
    unstub()


def generate_backend_stubs():
    """
    Mocking some calls to backend by mocking 'requests'
    """
    success_submit_response = mock({'status_code': 201, 'text': json.dumps({'id': str(existing_run)})})
    when(requests).post(f'{BASE_URL}/circuit/run', ...).thenReturn(success_submit_response)

    running_response = mock({'status_code': 200, 'text': json.dumps({'status': 'pending'})})
    success_get_response = mock({'status_code': 200, 'text': json.dumps(
        {'status': 'ready', 'measurements': {'result': [[1, 0, 1, 1], [1, 0, 0, 1], [1, 0, 1, 1], [1, 0, 1, 1]]}})})

    # run was not created response
    no_run_response = Response()
    no_run_response.status_code = 404
    no_run_response.reason = 'Run not found'

    when(requests).get(f'{BASE_URL}/circuit/run/{existing_run}', ...).\
        thenReturn(running_response).thenReturn(success_get_response)
    when(requests).get(f'{BASE_URL}/circuit/run/{missing_run}', ...).thenReturn(no_run_response)
