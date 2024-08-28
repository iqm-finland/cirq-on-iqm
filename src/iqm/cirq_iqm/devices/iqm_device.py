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
"""
Describes IQM quantum architectures in the Cirq framework.

The description includes the qubit connectivity, the native gate set, and the gate decompositions
to use with the architecture.
"""
# pylint: disable=protected-access,no-self-use
from __future__ import annotations

import collections.abc as ca
from itertools import zip_longest
from math import pi as PI
from typing import Optional, Sequence, cast
import uuid

import cirq
from cirq import InsertStrategy, MeasurementGate, devices, ops, protocols
from cirq.contrib.routing.router import nx

from iqm.cirq_iqm.iqm_gates import IQMMoveGate
from iqm.cirq_iqm.transpiler import transpile_insert_moves_into_circuit

from .iqm_device_metadata import IQMDeviceMetadata


def _verify_unique_measurement_keys(operations: ca.Iterable[cirq.Operation]) -> None:
    """Raises an error if a measurement key is repeated in the given set of Operations."""
    seen_keys: set[str] = set()
    for op in operations:
        if protocols.is_measurement(op):
            key = protocols.measurement_key_name(op)
            if key in seen_keys:
                raise ValueError(f'Measurement key {key} repeated')
            seen_keys.add(key)


def _validate_for_routing(circuit: cirq.AbstractCircuit) -> None:
    if not circuit.are_all_measurements_terminal():
        raise ValueError('Non-terminal measurements are not supported')


class IQMDevice(devices.Device):
    """ABC for the properties of a specific IQM quantum architecture.

    Adds extra functionality on top of the basic :class:`cirq.Device` class for decomposing gates,
    optimizing circuits and mapping qubits.

    Args:
        metadata: device metadata which contains the qubits, their connectivity, and the native gateset
    """

    def __init__(self, metadata: IQMDeviceMetadata):
        self._metadata = metadata
        self.qubits = tuple(sorted(self._metadata.qubit_set))
        self.resonators = tuple(sorted(self._metadata.resonator_set))
        self.supported_operations = self._metadata.operations

    @property
    def metadata(self) -> IQMDeviceMetadata:
        """Returns metadata for the device."""
        return self._metadata

    @classmethod
    def get_qubit_index(cls, qubit: cirq.NamedQubit) -> int:
        """The numeric index of the given qubit on the device."""
        return int(qubit.name[len(IQMDeviceMetadata.QUBIT_NAME_PREFIX) :])

    def get_qubit(self, index: int) -> cirq.Qid:
        """The device qubit corresponding to the given numeric index."""
        return self.qubits[index - 1]  # 1-based indexing

    def check_qubit_connectivity(self, operation: cirq.Operation) -> None:
        """Raises a ValueError if operation acts on qubits that are not connected."""
        if len(operation.qubits) >= 2 and not self.has_valid_operation_targets(operation):
            raise ValueError(f'Unsupported qubit connectivity required for {operation!r}')

    def is_native_operation(self, op: cirq.Operation) -> bool:
        """Predicate, True iff the given operation is considered native for the architecture."""
        check = (
            isinstance(op, (ops.GateOperation, ops.TaggedOperation))
            and (op.gate is not None)
            and (op.gate in self._metadata.gateset)
        )
        if check and isinstance(op.gate, ops.CZPowGate):
            return op.gate.exponent == 1
        return check

    def has_valid_operation_targets(self, op: cirq.Operation) -> bool:
        """Predicate, True iff the given operation is native and its targets are valid."""
        matched_support = [
            (g, qbs)
            for g, qbs in self.supported_operations.items()
            if op.gate is not None and op.gate in cirq.GateFamily(g)
        ]
        if len(matched_support) > 0:
            gf, valid_targets = matched_support[0]
            valid_qubits = set(q for qb in valid_targets for q in qb)
            if gf == cirq.MeasurementGate:  # Measurements can be done on any available qubits
                return all(q in valid_qubits for q in op.qubits)
            if issubclass(gf, cirq.InterchangeableQubitsGate):
                target_qubits = set(op.qubits)
                return any(set(t) == target_qubits for t in valid_targets)
            return any(all(q1 == q2 for q1, q2 in zip_longest(op.qubits, t)) for t in valid_targets)
        return False

    def operation_decomposer(self, op: cirq.Operation) -> Optional[list[cirq.Operation]]:
        """Decomposes operations into the native operation set.

        All the decompositions below keep track of global phase (required for decomposing controlled gates).

        Args:
            op: operation to decompose

        Returns:
            decomposition, or None to pass ``op`` to the Cirq native decomposition machinery instead
        """

        # It seems that Cirq native decompositions ignore global phase entirely?

        PI_2 = PI / 2

        # common gates used in gate decompositions
        CZ = ops.CZPowGate()
        Lx = ops.rx(PI_2)
        Lxi = ops.rx(-PI_2)
        Ly = ops.ry(PI_2)
        Lyi = ops.ry(-PI_2)

        if isinstance(op.gate, ops.CZPowGate):
            # decompose CZPowGate using ZZPowGate
            t = op.gate.exponent
            s = op.gate.global_shift
            L = ops.rz(t / 2 * PI)
            return [
                ops.ZZPowGate(exponent=-0.5 * t, global_shift=-2 * s - 1).on(*op.qubits),
                L.on(op.qubits[0]),
                L.on(op.qubits[1]),
            ]
        if isinstance(op.gate, ops.ZZPowGate):
            # decompose ZZPowGate using two CZs
            t = op.gate.exponent
            s = op.gate.global_shift
            return [
                Lyi.on(op.qubits[1]),
                CZ.on(*op.qubits),
                ops.XPowGate(exponent=-t, global_shift=-1 - s).on(op.qubits[1]),
                CZ.on(*op.qubits),
                Ly.on(op.qubits[1]),
            ]
        if isinstance(op.gate, ops.ISwapPowGate):
            # decompose ISwapPowGate using two CZs
            t = op.gate.exponent
            s = op.gate.global_shift
            x = -0.5 * t
            return [
                Lxi.on(op.qubits[0]),
                Lxi.on(op.qubits[1]),
                Lyi.on(op.qubits[1]),
                CZ.on(*op.qubits),
                ops.XPowGate(exponent=x, global_shift=-0.5 - 2 * s).on(op.qubits[0]),
                ops.XPowGate(exponent=-x, global_shift=-0.5).on(op.qubits[1]),
                CZ.on(*op.qubits),
                Ly.on(op.qubits[1]),
                Lx.on(op.qubits[0]),
                Lx.on(op.qubits[1]),
            ]
        if isinstance(op.gate, ops.ZPowGate):
            # Rz using Rx, Ry
            q = op.qubits[0]
            return [
                ops.XPowGate(exponent=-0.5).on(q),
                ops.YPowGate(exponent=op.gate.exponent).on(q),
                ops.XPowGate(exponent=0.5).on(q),
            ]
        return None

    def decompose_operation(self, operation: cirq.Operation) -> cirq.OP_TREE:
        """Decompose a single quantum operation into the native operation set."""
        if self.is_native_operation(operation):
            return operation

        return protocols.decompose(
            operation,
            intercepting_decomposer=self.operation_decomposer,
            keep=self.is_native_operation,
            on_stuck_raise=None,
        )

    def route_circuit(
        self,
        circuit: cirq.Circuit,
        *,
        initial_mapper: Optional[cirq.AbstractInitialMapper] = None,
        qubit_subset: Optional[Sequence[cirq.Qid]] = None,
    ) -> tuple[cirq.Circuit, dict[cirq.Qid, cirq.Qid], dict[cirq.Qid, cirq.Qid]]:
        """Routes the given circuit to the device connectivity and qubit names.

        The routed circuit uses the device qubits, and may have additional SWAP gates inserted to perform the qubit
        routing. The transformer :class:`cirq.RouterCQC` is used for routing.
        Note that only gates of one or two qubits, and measurement operations of arbitrary size are supported.

        Args:
            circuit: circuit to route
            initial_mapper: Initial mapping from ``circuit`` qubits to device qubits, to serve as
                the starting point of the routing. ``None`` means it will be generated automatically.

        Returns:
            The routed circuit.

            The initial mapping before inserting SWAP gates, see docstring of :func:`cirq.RouterCQC.route_circuit`

            The final mapping from physical qubits to physical qubits,
                see docstring of :func:`cirq.RouterCQC.route_circuit`

        Raises:
            ValueError: routing is impossible
        """
        _validate_for_routing(circuit)

        # Remove all measurement gates and replace them with 1-qubit identity gates so they don't
        # disappear from the final swap network if no other operations remain. We will add them back after routing the
        # rest of the network. This is done to prevent measurements becoming non-terminal during routing.
        measurement_ops = list(circuit.findall_operations_with_gate_type(MeasurementGate))
        measurement_qubits = set().union(*[op.qubits for _, op, _ in measurement_ops])

        modified_circuit = circuit.copy()
        modified_circuit.batch_remove([(ind, op) for ind, op, _ in measurement_ops])
        i_tag = uuid.uuid4()
        for q in measurement_qubits:
            modified_circuit.append(cirq.I(q).with_tags(i_tag))

        if self.metadata.resonator_set:
            move_routing = True
            graph = nx.Graph()
            for edge in self.metadata.nx_graph.edges:
                q, r = edge if edge[1] in self.resonators else edge[::-1]
                if r not in self.resonators:
                    graph.add_edge(*edge)
                else:
                    for n in self.metadata.nx_graph.neighbors(r):
                        if n != q and not graph.has_edge(q, n) and not graph.has_edge(n, q):
                            graph.add_edge(q, n)
        else:
            graph = self._metadata.nx_graph
            move_routing = False

        if qubit_subset is not None:
            graph = graph.subgraph(qubit_subset)

        # Route the modified circuit.
        router = cirq.RouteCQC(graph)
        routed_circuit, initial_mapping, final_mapping = router.route_circuit(
            modified_circuit, initial_mapper=initial_mapper
        )
        routed_circuit = cast(cirq.Circuit, routed_circuit)

        # Return measurements to the circuit with potential qubit swaps.
        new_measurements = []
        for _, op, gate in measurement_ops:
            new_qubits = [final_mapping[initial_mapping[q]] for q in op.qubits]
            new_measurement = cirq.measure(*new_qubits, key=gate.key)
            new_measurements.append(new_measurement)

        routed_circuit.append(new_measurements, InsertStrategy.NEW_THEN_INLINE)

        # Remove additional identity gates.
        identity_gates = routed_circuit.findall_operations(lambda op: i_tag in op.tags)
        routed_circuit.batch_remove(identity_gates)
        if move_routing:
            # Decompose the SWAP  gates to the native gate set.
            routed_circuit = self.decompose_circuit(routed_circuit)
            # Insert IQMMoveGates into the circuit.
            routed_circuit = transpile_insert_moves_into_circuit(routed_circuit, self)

        return routed_circuit, initial_mapping, final_mapping

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

    def validate_circuit(self, circuit: cirq.AbstractCircuit) -> None:
        super().validate_circuit(circuit)
        _verify_unique_measurement_keys(circuit.all_operations())
        _validate_for_routing(circuit)
        self.validate_moves(circuit)

    def validate_operation(self, operation: cirq.Operation) -> None:
        if not isinstance(operation.untagged, cirq.GateOperation):
            raise ValueError(f'Unsupported operation: {operation!r}')

        if not self.is_native_operation(operation):
            raise ValueError(f'Unsupported gate type: {operation.gate!r}')

        for qubit in operation.qubits:
            if qubit not in self.qubits and qubit not in self.resonators:
                raise ValueError(f'Qubit not on device: {qubit!r}')

        if not self.has_valid_operation_targets(operation):
            raise ValueError(f'Unsupported operation between qubits: {operation!r}')

    def validate_move(self, operation: cirq.Operation) -> None:
        """Validates whether the IQMMoveGate is between qubit and resonator registers.

        Args:
            operation (cirq.Operation): Operation to check

        Raises:
            ValueError: In case the the first argument of the IQMMoveGate is not a qubit,
                        or if the second argument is not a resonator on this device.

        Returns:
            None when the IQMMoveGate is used correctly.
        """
        if isinstance(operation.gate, IQMMoveGate):
            if operation.qubits[0] not in self.qubits:
                raise ValueError(
                    f'IQMMoveGate is only supported with a qubit register as the first argument, \
                    but got {operation.qubits[0]!r}'
                )
            if operation.qubits[1] not in self.resonators:
                raise ValueError(
                    f'IQMMoveGate is only supported with a resonator register as the second argument, \
                    but got {operation.qubits[1]!r}'
                )

    def validate_moves(self, circuit: cirq.AbstractCircuit) -> None:
        """Validates whether the IQMMoveGates are correctly applied in the circuit.

        Args:
            circuit (cirq.AbstractCircuit): The circuit to validate.

        Raises:
            ValueError: If the IQMMoveGate is applied incorrectly.
        Returns:
            None if the IQMMoveGates are applied correctly.
        """
        moves: dict[cirq.Qid, list[cirq.Qid]] = {r: [] for r in self.resonators}
        for moment in circuit:
            for operation in moment.operations:
                if isinstance(operation.gate, IQMMoveGate):
                    self.validate_move(operation)
                    moves[operation.qubits[1]].append(operation.qubits[0])
        for res, qubits in moves.items():
            while len(qubits) > 1:
                q1, q2, *rest = qubits
                if q1 != q2:
                    raise ValueError(f'IQMMoveGate({q2!r}, {res!r}) is applied between two logical qubit states.')
                qubits = rest
            if len(qubits) != 0:
                raise ValueError(f'Circuit ends with a qubit state in the resonator {res!r}.')

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self._metadata == other._metadata
