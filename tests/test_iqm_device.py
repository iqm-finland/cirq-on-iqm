# Copyright 2020–2022 Cirq on IQM developers
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
from cirq import NamedQid

from iqm.cirq_iqm import Adonis, Apollo, IQMDevice, Valkmusa


def test_equality_method():
    adonis_1 = Adonis()
    adonis_2 = Adonis()
    adonis_3 = Adonis()
    apollo_1 = Apollo()
    apollo_2 = Apollo()
    valkmusa = Valkmusa()
    adonis_3._metadata = valkmusa.metadata

    assert adonis_1 == adonis_2
    assert valkmusa != adonis_1
    assert apollo_1 == apollo_2
    assert adonis_2 != adonis_3


def test_device_without_resonator(device_without_resonator):
    assert_qubit_indexing(
        device_without_resonator,
        set(zip(range(1, len(device_without_resonator.qubits) + 1), device_without_resonator.qubits)),
    )
    assert len(device_without_resonator.resonators) == 0


def test_device_with_resonator(device_with_resonator):
    print(device_with_resonator.qubits)
    # Tests for device with resonator should pass too.
    assert_qubit_indexing(
        device_with_resonator, set(zip(range(1, len(device_with_resonator.qubits) + 1), device_with_resonator.qubits))
    )
    assert device_with_resonator.resonators[0] == NamedQid(
        "COMP_R", device_with_resonator._metadata.RESONATOR_DIMENSION
    )


def assert_qubit_indexing(backend: IQMDevice, correct_idx_name_associations):
    for idx, name in correct_idx_name_associations:
        print(idx, name, backend.get_qubit(idx), backend.get_qubit_index(name))
    assert all(backend.get_qubit(idx) == name for idx, name in correct_idx_name_associations)
    assert all(backend.get_qubit_index(name) == idx for idx, name in correct_idx_name_associations)
    # Below assertions are done in Qiskit but do not make sense for Cirq.
    # assert backend.index_to_qubit_name(7) is None
    # assert backend.qubit_name_to_index('Alice') is None
