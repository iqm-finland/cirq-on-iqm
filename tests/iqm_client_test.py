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
from cirq_iqm.iqm_client import IQMBackendClient, IQMCircuit, QubitMapping
from requests import HTTPError
from mockito import when, mock, unstub
import jsons
from tests.coco_mock import mock_backend

BASE_URL = "https://meetiqm.com/api/"
API_KEY = "random_key"


@pytest.fixture(scope="function", autouse=True)
def prepare():
    mock_backend()
    yield  # running test function
    unstub()


def test_submit_circuit():
    client = IQMBackendClient(BASE_URL, API_KEY)
    run_id = client.submit_circuit(
        mappings=[
            QubitMapping(logical_name="Qubit A", physical_name="qubit_1"),
            QubitMapping(logical_name="Qubit B", physical_name="qubit_2")
        ],
        circuit=jsons.load(
            {
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
            }, IQMCircuit), shots=1000)
    assert run_id == 14


def test_get_run_status():
    client = IQMBackendClient(BASE_URL, API_KEY)
    assert client.get_run(14).status == "pending"
    assert client.get_run(14).status == "ready"


def test_wrong_run():
    unstub()
    client = IQMBackendClient(BASE_URL, API_KEY)
    with pytest.raises(HTTPError):
        assert client.get_run(13)


def test_wait_results():
    client = IQMBackendClient(BASE_URL, API_KEY)
    assert client.wait_results(14).status == "ready"
