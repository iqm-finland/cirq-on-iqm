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
"""
Describes IQM quantum architectures in the Cirq framework.

The description includes the qubit connectivity, the native gate set, and the gate decompositions
to use with the architecture.
"""
# pylint: disable=protected-access
from __future__ import annotations

import abc
import collections.abc as ca
from typing import Optional, Union

import cirq
from cirq import devices, ops, protocols
from cirq.contrib.routing.router import nx, route_circuit


def _verify_unique_measurement_keys(operations: ca.Iterable[cirq.Operation]) -> None:
    """Raises an error if a measurement key is repeated in the given set of Operations.
    """
    seen_keys: set[str] = set()
    for op in operations:
        if protocols.is_measurement(op):
            key = protocols.measurement_key(op)
            if key in seen_keys:
                raise ValueError(f'Measurement key {key} repeated')
            seen_keys.add(key)


class IQMDevice(devices.Device):
    """ABC for the properties of a specific IQM quantum architecture.

    Adds extra functionality on top of the basic :class:`cirq.Device` class for decomposing gates,
    optimizing circuits and mapping qubits.
    """
    QUBIT_COUNT: int = None
    """number of qubits on the device"""

    QUBIT_NAME_PREFIX: str = 'QB'
    """prefix for qubit names, to be followed by their numerical index"""

    CONNECTIVITY: tuple[set[int]] = ()
    """qubit connectivity graph of the device"""

    NATIVE_GATES: tuple[type[cirq.Gate]] = ()
    """native gate set of the device (gate families)"""

    NATIVE_GATE_INSTANCES: tuple[cirq.Gate] = ()
    """native gate set of the device (individual gates)"""

    def __init__(self):
        self.qubits = tuple(cirq.NamedQubit.range(1, self.QUBIT_COUNT + 1, prefix=self.QUBIT_NAME_PREFIX))

    @classmethod
    def get_qubit_index(cls, qubit: cirq.NamedQubit) -> int:
        """The numeric index of the given qubit on the device."""
        return int(qubit.name[len(cls.QUBIT_NAME_PREFIX):])

    def get_qubit(self, index: int) -> cirq.NamedQubit:
        """The device qubit corresponding to the given numeric index."""
        return self.qubits[index - 1]  # 1-based indexing

    @classmethod
    def check_qubit_connectivity(cls, operation: cirq.Operation) -> None:
        """Raises a ValueError if operation acts on qubits that are not connected.
        """
        if len(operation.qubits) >= 2 and not isinstance(operation.gate, ops.MeasurementGate):
            connection = set(cls.get_qubit_index(q) for q in operation.qubits)
            if connection not in cls.CONNECTIVITY:
                raise ValueError(f'Unsupported qubit connectivity required for {operation!r}')

    @classmethod
    def is_native_operation(cls, op: cirq.Operation) -> bool:
        """Predicate, True iff the given operation is considered native for the architecture."""
        return (
            isinstance(op, (ops.GateOperation, ops.TaggedOperation))
            and (
                isinstance(op.gate, cls.NATIVE_GATES)
                or op.gate in cls.NATIVE_GATE_INSTANCES
            )
        )

    @abc.abstractmethod
    def operation_decomposer(self, op: cirq.Operation) -> Optional[list[cirq.Operation]]:
        """Decomposes operations into the native operation set.

        Operations are decomposed immediately when they are inserted into a Circuit associated with an IQMDevice.

        Args:
            op: operation to decompose

        Returns:
            decomposition, or None to pass ``op`` to the Cirq native decomposition machinery instead
        """

    def decompose_operation(self, operation: cirq.Operation) -> cirq.OP_TREE:
        if self.is_native_operation(operation):
            return operation

        return protocols.decompose(
            operation,
            intercepting_decomposer=self.operation_decomposer,
            keep=self.is_native_operation,
            on_stuck_raise=None
        )

    def route_circuit(
            self,
            circuit: cirq.Circuit,
            *,
            return_swap_network: bool = False
    ) -> Union[cirq.Circuit, cirq.contrib.routing.SwapNetwork]:
        """Routes the given circuit to the device connectivity.

        The routed circuit uses the device qubits, and may have additional SWAP gates inserted
        to perform the qubit routing.

        Args:
            circuit: circuit to route
            return_swap_network: iff True, return the full swap network instead of the routed circuit

        Returns:
            routed circuit, or the swap network if requested

        Raises:
            ValueError: routing is impossible
        """
        device_graph = nx.Graph(tuple(map(self.get_qubit, edge)) for edge in self.CONNECTIVITY)
        swap_network = route_circuit(circuit, device_graph, algo_name='greedy')
        if return_swap_network:
            return swap_network
        return swap_network.circuit

    def decompose_circuit(self, circuit: cirq.Circuit) -> cirq.Circuit:
        """Decomposes the given circuit to the native gate set of the device.

        Args:
            circuit: circuit to decompose

        Returns:
            decomposed circuit
        """
        moments = ops.transform_op_tree(
            circuit.moments,
            self.decompose_operation,
            preserve_moments=False,
        )
        return cirq.Circuit(moments)

    def validate_circuit(self, circuit: cirq.Circuit) -> None:
        super().validate_circuit(circuit)
        _verify_unique_measurement_keys(circuit.all_operations())

    def validate_operation(self, operation: cirq.Operation) -> None:
        if not isinstance(operation.untagged, cirq.GateOperation):
            raise ValueError(f'Unsupported operation: {operation!r}')

        if not self.is_native_operation(operation):
            raise ValueError(f'Unsupported gate type: {operation.gate!r}')

        for qubit in operation.qubits:
            if qubit not in self.qubits:
                raise ValueError(f'Qubit not on device: {qubit!r}')

        self.check_qubit_connectivity(operation)

    def __eq__(self, other):
        return self.__class__ == other.__class__
