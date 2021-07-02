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

# pylint: disable=unused-argument
import json
import pytest

import cirq

from cirq_iqm.iqm_client import SingleQubitMappingDTO
from cirq_iqm.iqm_device import IQMQubit
from cirq_iqm.iqm_remote import IQMSampler


@pytest.fixture()
def qubit_mapping():
    return {
        'q1 log.': 'q1 phys.',
        'q2 log.': 'q2 phys.'
    }


def test_transforms_qubit_mapping(qubit_mapping):
    sampler = IQMSampler('example.com', '{"stuff": "some settings"}', qubit_mapping)
    assert sampler._qubit_mapping == [
        SingleQubitMappingDTO(logical_name='q1 log.', physical_name='q1 phys.'),
        SingleQubitMappingDTO(logical_name='q2 log.', physical_name='q2 phys.'),
    ]


def test_run_sweep_executes_circuit(mock_server, settings_dict, base_url, qubit_mapping):
    sampler = IQMSampler(base_url, json.dumps(settings_dict), qubit_mapping)
    qubit = IQMQubit(1)
    circuit = cirq.Circuit(
        cirq.measure(qubit, key='result')
    )
    results = sampler.run_sweep(circuit, None, repetitions=2)
    assert isinstance(results[0], cirq.Result)
