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

from typing import FrozenSet, Optional, Type, Union

import cirq
from cirq import NamedQubit, devices, ops
from cirq.contrib.routing.router import nx
from iqm_client import QuantumArchitectureSpecification

# Mapping from IQM operation names to cirq operations
_IQM_CIRQ_OP_MAP: dict[str, Optional[tuple[Union[Type[cirq.Gate], cirq.Gate, cirq.GateFamily], ...]]] = {
    # XPow and YPow kept for convenience, Cirq does not know how to decompose them into PhasedX
    # so we would have to add those rules...
    'phased_rx': (cirq.ops.PhasedXPowGate, cirq.ops.XPowGate, cirq.ops.YPowGate),
    'cz': (cirq.ops.CZ,),
    'measurement': (cirq.ops.MeasurementGate,),
    'barrier': None,
}


@cirq.value.value_equality
class IQMDeviceMetadata(devices.DeviceMetadata):
    """Hardware metadata for IQM devices.

    Args:
        qubits: frozenset of qubits that exist on the device
        connectivity: qubit connectivity graph of the device
        gateset: Native gateset of the device. If None, a default IQM device gateset will be used.
    """

    QUBIT_NAME_PREFIX: str = 'QB'
    """prefix for qubit names, to be followed by their numerical index"""

    def __init__(  # pylint: disable=super-init-not-called
        self,
        qubits: FrozenSet[cirq.NamedQubit],
        connectivity: tuple[set[int], ...],
        gateset: Optional[cirq.Gateset] = None,
    ):
        """Construct an IQMDeviceMetadata object."""
        nx_graph = nx.Graph()
        for edge in connectivity:
            edge_qubits = [NamedQubit(f'{self.QUBIT_NAME_PREFIX}{q}') for q in edge]
            nx_graph.add_edge(edge_qubits[0], edge_qubits[1])
        self._qubits_set: FrozenSet[cirq.NamedQubit] = frozenset(qubits)
        self._nx_graph = nx_graph

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
        qubits = frozenset(cirq.NamedQubit(qb) for qb in architecture.qubits)
        connectivity = tuple(
            {int(qb.removeprefix(IQMDeviceMetadata.QUBIT_NAME_PREFIX)) for qb in edge}
            for edge in architecture.qubit_connectivity
        )
        gateset = cirq.Gateset(
            *tuple(
                cirq_op
                for iqm_op in architecture.operations
                if (cirq_ops := _IQM_CIRQ_OP_MAP[iqm_op]) is not None
                for cirq_op in cirq_ops
            )
        )
        return IQMDeviceMetadata(qubits, connectivity, gateset)

    @property
    def qubit_set(self) -> FrozenSet[cirq.NamedQubit]:
        """Returns the set of qubits on the device."""
        return self._qubits_set

    @property
    def gateset(self) -> cirq.Gateset:
        """Returns the ``cirq.Gateset`` of supported gates on this device."""
        return self._gateset

    def _value_equality_values_(self):
        graph_equality = (
            tuple(sorted(self._nx_graph.nodes())),
            tuple(sorted(self._nx_graph.edges(data='directed'))),
        )
        return self._qubits_set, graph_equality, self._gateset
