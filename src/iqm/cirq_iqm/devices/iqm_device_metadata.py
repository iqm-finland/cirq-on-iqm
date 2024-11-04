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
from iqm.iqm_client import DynamicQuantumArchitecture


@cirq.value.value_equality
class IQMDeviceMetadata(devices.DeviceMetadata):
    """Hardware metadata for IQM devices.

    Args:
        qubits: qubits on the device
        connectivity: qubit connectivity graph of the device
        operations: Supported quantum operations of the device, mapping op types to their possible loci.
        gateset: Native gateset of the device. If None, a default IQM device gateset will be used.
        resonators: computational resonators of the device
        architecture: architecture from which values of the other arguments were obtained
    """

    QUBIT_NAME_PREFIX: str = 'QB'
    """prefix for qubit names, to be followed by their numerical index"""

    RESONATOR_DIMENSION: int = 2
    """Dimension abstraction for the resonator Qids"""

    def __init__(
        self,
        qubits: Iterable[NamedQid],
        connectivity: Iterable[tuple[NamedQid, ...]],
        *,
        operations: Optional[dict[type[cirq.Gate], list[tuple[cirq.NamedQid, ...]]]] = None,
        gateset: Optional[cirq.Gateset] = None,
        resonators: Iterable[NamedQid] = (),
        architecture: Optional[DynamicQuantumArchitecture] = None,
    ):
        """Construct an IQMDeviceMetadata object."""
        nx_graph = nx.Graph()
        for edge in connectivity:
            if len(edge) != 2:
                raise ValueError('Connectivity must be an iterable of 2-tuples.')
            nx_graph.add_edge(edge[0], edge[1])
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

        self.architecture = architecture

    @property
    def resonator_set(self) -> FrozenSet[NamedQid]:
        """Returns the set of resonators on the device.

        Returns:
            Frozenset of resonators on device.
        """
        return self._resonator_set

    @classmethod
    def from_architecture(cls, architecture: DynamicQuantumArchitecture) -> IQMDeviceMetadata:
        """Returns device metadata object created based on dynamic quantum architecture"""
        qubits = tuple(NamedQid(qb, dimension=2) for qb in architecture.qubits)
        resonators = tuple(
            NamedQid(cr, dimension=cls.RESONATOR_DIMENSION) for cr in architecture.computational_resonators
        )

        def get_qid_locus(locus: Iterable[str]) -> tuple[NamedQid, ...]:
            """Converts locus component names to Qids."""
            return tuple(
                (
                    NamedQid(component, dimension=2)
                    if component in qubits
                    else NamedQid(component, dimension=cls.RESONATOR_DIMENSION)
                )
                for component in locus
            )

        # connectivity consists of all arity-2 gate loci in the DQA
        connectivity = tuple(
            get_qid_locus(locus)
            for gate_info in architecture.gates.values()
            for locus in gate_info.loci
            if len(locus) == 2
        )
        operations: dict[type[cirq.Gate], list[tuple[NamedQid, ...]]] = {
            cirq_op: [get_qid_locus(locus) for locus in gate_info.loci]
            for gate_name, gate_info in architecture.gates.items()
            if gate_name in _IQM_CIRQ_OP_MAP
            for cirq_op in _IQM_CIRQ_OP_MAP[gate_name]
        }
        return cls(
            qubits,
            connectivity,
            operations=operations,
            resonators=resonators,
            architecture=architecture,
        )

    @classmethod
    def from_qubit_indices(
        cls,
        qubit_count: int,
        connectivity_indices: Iterable[set[int]],
        gateset: Optional[tuple[type[cirq.Gate]]] = None,
    ) -> IQMDeviceMetadata:
        """Returns device metadata object created based on connectivity specified using qubit indices only."""
        qubits = tuple(NamedQid.range(1, qubit_count + 1, prefix=cls.QUBIT_NAME_PREFIX, dimension=2))
        if set(map(len, connectivity_indices)) != {2}:
            raise ValueError('connectivity_indices must be an iterable of 2-sets.')
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
