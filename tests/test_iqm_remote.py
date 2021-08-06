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
from cirq_iqm.iqm_remote import IQMSampler, serialize_qubit_mapping
from cirq_iqm import Adonis
from cirq_iqm.valkmusa import Valkmusa


@pytest.fixture()
def circuit():
    qubit_1 = cirq.NamedQubit('q1 log.')
    qubit_2 = cirq.NamedQubit('q2 log.')
    return cirq.Circuit(
        cirq.measure(qubit_1, qubit_2, key='result')
    )


@pytest.fixture()
def qubit_mapping():
    return {
        'q1 log.': 'QB1',
        'q2 log.': 'QB2'
    }


@pytest.fixture()
def adonis_sampler(base_url, settings_dict, qubit_mapping):
    return IQMSampler(base_url, json.dumps(settings_dict), Adonis(), qubit_mapping)


def test_serialize_qubit_mapping(qubit_mapping):
    assert serialize_qubit_mapping(qubit_mapping) == [
        SingleQubitMappingDTO(logical_name='q1 log.', physical_name='QB1'),
        SingleQubitMappingDTO(logical_name='q2 log.', physical_name='QB2'),
    ]


def test_run_sweep_executes_circuit(mock_server, adonis_sampler, circuit):
    results = adonis_sampler.run_sweep(circuit, None, repetitions=2)
    assert isinstance(results[0], cirq.Result)


def test_circuit_with_incorrect_device(adonis_sampler):
    circuit = cirq.Circuit(device=Valkmusa())
    with pytest.raises(ValueError, match='devices .* not the same'):
        adonis_sampler.run(circuit)


def test_non_injective_qubit_mapping(base_url, settings_dict, qubit_mapping):
    qubit_mapping['q2 log.'] = 'QB1'

    with pytest.raises(ValueError, match='Multiple logical qubits map to the same physical qubit'):
        IQMSampler(base_url, json.dumps(settings_dict), Adonis(), qubit_mapping)


def test_qubits_not_in_settings(circuit, base_url, settings_dict, qubit_mapping):
    del settings_dict['subtrees']['QB1']
    with pytest.raises(
            ValueError,
            match="The physical qubits {'QB1'} in the qubit mapping are not defined in the settings"
    ):
        IQMSampler(base_url, json.dumps(settings_dict), Adonis(), qubit_mapping)


def test_incomplete_qubit_mapping(adonis_sampler, circuit):
    new_qubit = cirq.NamedQubit('Eve')
    circuit.append(cirq.X(new_qubit))

    with pytest.raises(ValueError, match="The qubits {'Eve'} are not found in the provided qubit mapping"):
        adonis_sampler.run(circuit)
