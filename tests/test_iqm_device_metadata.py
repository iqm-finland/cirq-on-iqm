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

import cirq
from iqm_client.iqm_client import QuantumArchitectureSpecification

from cirq_iqm import IQMDeviceMetadata


def test_device_metadata_from_architecture():
    qa = {
        'name': 'Valkmusa',
        'operations': [
            'phased_rx',
            'measurement',
        ],
        'qubits': ['QB1', 'QB2'],
        'qubit_connectivity': [
            ['QB1', 'QB2'],
        ],
    }
    metadata = IQMDeviceMetadata.from_architecture(QuantumArchitectureSpecification(**qa))
    assert metadata.qubit_set == {cirq.NamedQubit('QB1'), cirq.NamedQubit('QB2')}
    assert [set(e) for e in metadata.nx_graph.edges] == [{cirq.NamedQubit('QB1'), cirq.NamedQubit('QB2')}]
    assert metadata.gateset == cirq.Gateset(cirq.PhasedXPowGate, cirq.XPowGate, cirq.YPowGate, cirq.MeasurementGate)
