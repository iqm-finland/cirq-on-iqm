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
"""DeviceMetadata subtype for IQM devices."""
from __future__ import annotations

from collections.abc import Iterable
from typing import Optional, Union

import cirq
from cirq import NamedQubit, Qid, devices, ops
from cirq.contrib.routing.router import nx
from iqm_client import QuantumArchitectureSpecification

# Mapping from IQM operation names to cirq operations
_IQM_CIRQ_OP_MAP: dict[str, tuple[Union[type[cirq.Gate], cirq.Gate, cirq.GateFamily], ...]] = {
    # XPow and YPow kept for convenience, Cirq does not know how to decompose them into PhasedX
    # so we would have to add those rules...
    'phased_rx': (cirq.ops.PhasedXPowGate, cirq.ops.XPowGate, cirq.ops.YPowGate),
    'cz': (cirq.ops.CZ,),
    'measurement': (cirq.ops.MeasurementGate,),
    'barrier': (),
}


@cirq.value.value_equality
class IQMDeviceMetadata(devices.DeviceMetadata):
    """Hardware metadata for IQM devices.

    Args:
        qubits: qubits that exist on the device
        connectivity: qubit connectivity graph of the device
        gateset: Native gateset of the device. If None, a default IQM device gateset will be used.
    """

    QUBIT_NAME_PREFIX: str = 'QB'
    """prefix for qubit names, to be followed by their numerical index"""

    def __init__(
        self,
        qubits: Iterable[Qid],
        connectivity: Iterable[Iterable[Qid]],
        gateset: Optional[cirq.Gateset] = None,
    ):
        """Construct an IQMDeviceMetadata object."""
        nx_graph = nx.Graph()
        for edge in connectivity:
            edge_qubits = list(edge)
            nx_graph.add_edge(edge_qubits[0], edge_qubits[1])
        super().__init__(qubits, nx_graph)

        if gateset is None:
            # default gateset for IQM devices
            self._gateset = cirq.Gateset(
                ops.PhasedXPowGate, ops.XPowGate, ops.YPowGate, ops.MeasurementGate, ops.CZPowGate()
            )
        else:
            self._gateset = gateset

    @classmethod
    def from_architecture(cls, architecture: QuantumArchitectureSpecification) -> IQMDeviceMetadata:
        """Returns device metadata object created based on architecture specification"""
        qubits = tuple(NamedQubit(qb) for qb in architecture.qubits)
        connectivity = tuple(tuple(NamedQubit(qb) for qb in edge) for edge in architecture.qubit_connectivity)
        gateset = cirq.Gateset(*(cirq_op for iqm_op in architecture.operations for cirq_op in _IQM_CIRQ_OP_MAP[iqm_op]))
        return cls(qubits, connectivity, gateset)

    @classmethod
    def from_qubit_indices(
        cls, qubit_count: int, connectivity_indices: tuple[set[int], ...], gateset: Optional[cirq.Gateset] = None
    ) -> IQMDeviceMetadata:
        """Returns device metadata object created based on connectivity specified using qubit indices only."""
        qubits = tuple(NamedQubit.range(1, qubit_count + 1, prefix=cls.QUBIT_NAME_PREFIX))
        connectivity = tuple(
            tuple(NamedQubit(f'{cls.QUBIT_NAME_PREFIX}{qb}') for qb in edge) for edge in connectivity_indices
        )
        return cls(qubits, connectivity, gateset)

    @property
    def gateset(self) -> cirq.Gateset:
        """Returns the ``cirq.Gateset`` of supported gates on this device."""
        return self._gateset

    def _value_equality_values_(self):
        return *super()._value_equality_values_(), self._gateset
