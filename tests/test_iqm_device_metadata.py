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
from uuid import UUID

import cirq
import pytest

from iqm.cirq_iqm import IQMDeviceMetadata
from iqm.iqm_client import DynamicQuantumArchitecture, GateImplementationInfo, GateInfo


def test_device_metadata_from_architecture():
    arch = DynamicQuantumArchitecture(
        calibration_set_id=UUID('26c5e70f-bea0-43af-bd37-6212ec7d04cb'),
        qubits=['QB1', 'QB2'],
        computational_resonators=[],
        gates={
            'prx': GateInfo(
                implementations={
                    'drag_gaussian': GateImplementationInfo(loci=(('QB1',), ('QB2',))),
                },
                default_implementation='drag_gaussian',
                override_default_implementation={},
            ),
            'cz': GateInfo(
                implementations={
                    'tgss': GateImplementationInfo(loci=(('QB1', 'QB2'),)),
                },
                default_implementation='tgss',
                override_default_implementation={},
            ),
            'measure': GateInfo(
                implementations={
                    'constant': GateImplementationInfo(loci=(('QB1',), ('QB2',))),
                },
                default_implementation='constant',
                override_default_implementation={},
            ),
        },
    )
    metadata = IQMDeviceMetadata.from_architecture(arch)
    assert metadata.qubit_set == {cirq.NamedQubit('QB1'), cirq.NamedQubit('QB2')}
    assert [set(e) for e in metadata.nx_graph.edges] == [{cirq.NamedQubit('QB1'), cirq.NamedQubit('QB2')}]
    assert metadata.gateset == cirq.Gateset(
        cirq.PhasedXPowGate, cirq.XPowGate, cirq.YPowGate, cirq.MeasurementGate, cirq.CZPowGate
    )


def test_device_metadata_qubit_indices_bad_connectivity():
    with pytest.raises(ValueError, match='connectivity_indices must be an iterable of 2-sets'):
        IQMDeviceMetadata.from_qubit_indices(3, [{1, 2}, {2, 3}, {1, 2, 3}])


def test_device_metadata_init_bad_connectivity():
    qubits = [cirq.NamedQubit(f'QB{q}') for q in range(3)]
    with pytest.raises(ValueError, match='Connectivity must be an iterable of 2-tuples'):
        IQMDeviceMetadata(qubits, [(qubits[0], qubits[1]), (qubits[0], qubits[1], qubits[2])])
