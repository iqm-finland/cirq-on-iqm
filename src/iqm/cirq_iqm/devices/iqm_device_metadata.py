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
from typing import FrozenSet, Optional

import cirq
from cirq import Gate, NamedQid, devices, ops
from cirq.contrib.routing.router import nx

from iqm.cirq_iqm.iqm_operation_mapping import _IQM_CIRQ_OP_MAP
from iqm.iqm_client import QuantumArchitectureSpecification


@cirq.value.value_equality
class IQMDeviceMetadata(devices.DeviceMetadata):
    """Hardware metadata for IQM devices.

    Args:
        qubits: qubits on the device
        connectivity: qubit connectivity graph of the device
        operations: Supported quantum operations of the device, mapping op types to their possible loci.
        gateset: Native gateset of the device. If None, a default IQM device gateset will be used.
        resonators: computational resonators of the device
    """

    QUBIT_NAME_PREFIX: str = 'QB'
    """prefix for qubit names, to be followed by their numerical index"""

    RESONATOR_DIMENSION: int = 2
    """Dimension abstraction for the resonator Qids"""

    def __init__(
        self,
        qubits: Iterable[NamedQid],
        connectivity: Iterable[Iterable[NamedQid]],
        *,
        operations: Optional[dict[type[cirq.Gate], list[tuple[cirq.NamedQid, ...]]]] = None,
        gateset: Optional[cirq.Gateset] = None,
        resonators: Iterable[NamedQid] = (),
    ):
        """Construct an IQMDeviceMetadata object."""
        nx_graph = nx.Graph()
        for edge in connectivity:
            edge_qubits = list(edge)
            nx_graph.add_edge(edge_qubits[0], edge_qubits[1])
        super().__init__(qubits, nx_graph)
        self._qubit_set: FrozenSet[NamedQid] = frozenset(qubits)
        self._resonator_set: FrozenSet[NamedQid] = frozenset(resonators)

        if gateset is None:
            if operations is None:
                # default gateset for IQM devices
                gateset = cirq.Gateset(
                    ops.PhasedXPowGate, ops.XPowGate, ops.YPowGate, ops.MeasurementGate, ops.CZPowGate
                )
                sqg_list: list[type[Gate]] = [ops.PhasedXPowGate, ops.XPowGate, ops.YPowGate, ops.MeasurementGate]
                operations = {}
                operations[ops.CZPowGate] = list(tuple(edge) for edge in connectivity)
                operations.update({gate: [(qb,) for qb in qubits] for gate in sqg_list})
            else:
                gateset = cirq.Gateset(*operations.keys())
        self._gateset = gateset

        if operations is None:
            raise ValueError('Operations must be provided if a gateset is provided, it cannot be reconstructed.')
        self.operations = operations

    @property
    def resonator_set(self) -> FrozenSet[NamedQid]:
        """Returns the set of resonators on the device.

        Returns:
            Frozenset of resonators on device.
        """
        return self._resonator_set

    @classmethod
    def from_architecture(cls, architecture: QuantumArchitectureSpecification) -> IQMDeviceMetadata:
        """Returns device metadata object created based on architecture specification"""
        qubits = tuple(NamedQid(qb, dimension=2) for qb in architecture.qubits if qb.startswith(cls.QUBIT_NAME_PREFIX))
        resonators = tuple(
            NamedQid(qb, dimension=cls.RESONATOR_DIMENSION)
            for qb in architecture.qubits
            if not qb.startswith(cls.QUBIT_NAME_PREFIX)
        )
        connectivity = tuple(
            tuple(
                (
                    NamedQid(qb, dimension=2)
                    if qb.startswith(cls.QUBIT_NAME_PREFIX)
                    else NamedQid(qb, dimension=cls.RESONATOR_DIMENSION)
                )
                for qb in edge
            )
            for edge in architecture.qubit_connectivity
        )
        operations: dict[type[cirq.Gate], list[tuple[NamedQid, ...]]] = {
            cirq_op: [
                tuple(
                    (
                        NamedQid(qb, dimension=2)
                        if qb.startswith(cls.QUBIT_NAME_PREFIX)
                        else NamedQid(qb, dimension=cls.RESONATOR_DIMENSION)
                    )
                    for qb in args
                )
                for args in qubits
            ]
            for iqm_op, qubits in architecture.operations.items()
            for cirq_op in _IQM_CIRQ_OP_MAP[iqm_op]
        }
        return cls(qubits, connectivity, operations=operations, resonators=resonators)

    def to_architecture(self) -> QuantumArchitectureSpecification:
        """Returns the architecture specification object created based on device metadata."""
        qubits = tuple(qb.name for qb in self._qubit_set)
        resonators = tuple(qb.name for qb in self.resonator_set)
        connectivity = tuple(tuple(qb.name for qb in edge) for edge in self.nx_graph.edges())
        operations: dict[str, list[tuple[str, ...]]] = {
            iqm_op: [tuple(qb.name for qb in args) for args in qubits]
            for cirq_op, qubits in self.operations.items()
            for iqm_op, cirq_ops in _IQM_CIRQ_OP_MAP.items()
            if cirq_op in cirq_ops
        }
        return QuantumArchitectureSpecification(
            name='From Cirq object', qubits=resonators + qubits, qubit_connectivity=connectivity, operations=operations
        )

    @classmethod
    def from_qubit_indices(
        cls,
        qubit_count: int,
        connectivity_indices: tuple[set[int], ...],
        gateset: Optional[tuple[type[cirq.Gate]]] = None,
    ) -> IQMDeviceMetadata:
        """Returns device metadata object created based on connectivity specified using qubit indices only."""
        qubits = tuple(NamedQid.range(1, qubit_count + 1, prefix=cls.QUBIT_NAME_PREFIX, dimension=2))
        connectivity = tuple(
            tuple(NamedQid(f'{cls.QUBIT_NAME_PREFIX}{qb}', dimension=2) for qb in edge) for edge in connectivity_indices
        )
        if gateset:
            sqg_list: list[type[Gate]] = [
                g for g in gateset if g in [ops.PhasedXPowGate, ops.XPowGate, ops.YPowGate, ops.MeasurementGate]
            ]
            operations: dict[type[cirq.Gate], list[tuple[cirq.NamedQid, ...]]] = {}
            if ops.CZPowGate in gateset:
                operations[ops.CZPowGate] = list(tuple(edge) for edge in connectivity)
            if ops.ISwapPowGate in gateset:
                operations[ops.ISwapPowGate] = list(tuple(edge) for edge in connectivity)
            operations.update({gate: [(qb,) for qb in qubits] for gate in sqg_list})
            return cls(qubits, connectivity, operations=operations, gateset=cirq.Gateset(*gateset))
        return cls(qubits, connectivity)

    @property
    def gateset(self) -> cirq.Gateset:
        """Returns the ``cirq.Gateset`` of supported gates on this device."""
        return self._gateset

    def _value_equality_values_(self):
        return *super()._value_equality_values_(), self._gateset
