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
import requests
from mockito import when, mock

BASE_URL = 'https://meetiqm.com/api/'


def mock_backend():
    """
    Mocking some calls to backend by mocking 'requests'
    """
    success_submit_response = mock({'status_code': 201, 'text': json.dumps({'id': 14})})
    when(requests).post(f'{BASE_URL}/circuit/run', ...).thenReturn(success_submit_response)

    running_response = mock({'status_code': 200, 'text': json.dumps({'status': 'pending'})})
    success_get_response = mock({'status_code': 200, 'text': json.dumps(
        {'status': 'ready', 'measurements': {'result': [[1, 0, 1, 1], [1, 0, 0, 1], [1, 0, 1, 1], [1, 0, 1, 1]]}})})
    no_run_response = mock({'status_code': 404, 'text': 'Run not found'})

    when(requests).get(f'{BASE_URL}/circuit/run/14', ...).thenReturn(running_response).thenReturn(success_get_response)
    when(requests).get(f'{BASE_URL}/circuit/run/13', ...).thenReturn(no_run_response)
