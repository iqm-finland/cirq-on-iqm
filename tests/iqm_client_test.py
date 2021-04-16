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

"""Testing IQM api client."""
import json

import pytest
from cirq_iqm.iqm_client import IQMBackendClient
from mockito import when, mock, unstub
import requests
from requests import HTTPError

BASE_URL = "https://meetiqm.com/api/"
api_key = "random_key"


@pytest.fixture(scope="function", autouse=True)
def prepare():
    success_submit_response = mock({'status_code': 201, 'text': json.dumps({"id": 14})})
    when(requests).post(f"{BASE_URL}/circuit/run", ...).thenReturn(success_submit_response)

    running_response = mock({'status_code': 200, 'text': json.dumps({"status": "pending"})})
    success_get_response = mock({'status_code': 200, 'text': json.dumps({"status": "ready", "results": "0101010101"})})
    no_run_response = mock({'status_code': 404, 'text': "Run not found"})

    when(requests).get(f"{BASE_URL}/circuit/run/14", ...).thenReturn(running_response).thenReturn(success_get_response)
    when(requests).get(f"{BASE_URL}/circuit/run/13", ...).thenReturn(no_run_response)

    yield  # running test function

    unstub()


mapping = dict()


def test_submit_circuit():
    client = IQMBackendClient(api_key)
    run_id = client.submit_circuit({"Qubit A": "qubit_1", "Qubit B": "qubit_2"}, {
        "name": "The circuit",
        "args": {
            "alpha": 1.2
        },
        "instructions": [
            {
                "name": "cz",
                "qubits": [
                    "Qubit A",
                    "Qubit B"
                ],
                "args": {}
            },
            {
                "name": "rotation",
                "qubits": [
                    "Qubit A"
                ],
                "args": {
                    "phase_t": 1.22,
                    "angle_t": {
                        "expr": "{{alpha}}/2"
                    }
                }
            },
            {
                "name": "measurement",
                "qubits": [
                    "Qubit A"
                ],
                "args": {
                    "output_label": "A"
                }
            }
        ]
    }, shots=1000)
    assert run_id == 14


def test_get_run_status():
    client = IQMBackendClient(api_key)
    assert client.get_run_status(14)["status"] == "pending"
    assert client.get_run_status(14)["status"] == "ready"


def test_wrong_run():
    unstub()
    client = IQMBackendClient(api_key)
    with pytest.raises(HTTPError):
        assert client.get_run_status(13)


def test_wait_results():
    client = IQMBackendClient(api_key)
    assert client.wait_results(14)["status"] == "ready"
