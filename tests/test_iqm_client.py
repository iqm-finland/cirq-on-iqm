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
"""Tests for the IQM client.
"""
# pylint: disable=unused-argument
from uuid import UUID

import pytest
from requests import HTTPError

from cirq_iqm.iqm_client import (CircuitDTO, IQMClient, RunStatus,
                                 SingleQubitMappingDTO)

existing_run = UUID("3c3fcda3-e860-46bf-92a4-bcc59fa76ce9")
missing_run = UUID("059e4186-50a3-4e6c-ba1f-37fe6afbdfc2")


def test_submit_circuit_returns_id(mock_server, settings_dict, base_url):
    """
    Tests sending a circuit
    """
    client = IQMClient(base_url, settings_dict)
    run_id = client.submit_circuit(
        qubit_mapping=[
            SingleQubitMappingDTO(logical_name="Qubit A", physical_name="qubit_1"),
            SingleQubitMappingDTO(logical_name="Qubit B", physical_name="qubit_2")
        ],
        circuit=CircuitDTO.parse_obj(
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
            }),
        shots=1000)
    assert run_id == existing_run


def test_get_run_status_for_existing_run(mock_server, base_url, settings_dict):
    """
    Tests getting the run status
    """
    client = IQMClient(base_url, settings_dict)
    assert client.get_run(existing_run).status == RunStatus.PENDING
    assert client.get_run(existing_run).status == RunStatus.READY


def test_get_run_status_for_missing_run(mock_server, base_url, settings_dict):
    """
    Tests getting a task that was not created
    """
    client = IQMClient(base_url, settings_dict)
    with pytest.raises(HTTPError):
        assert client.get_run(missing_run)


def test_waiting_for_results(mock_server, base_url, settings_dict):
    """
    Tests waiting for results for an existing task
    """
    client = IQMClient(base_url, settings_dict)
    assert client.wait_for_results(existing_run).status == RunStatus.READY
