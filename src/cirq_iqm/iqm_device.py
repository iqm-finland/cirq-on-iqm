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
and circuit optimization methods to use with the architecture.
"""
# pylint: disable=protected-access
from __future__ import annotations

import abc
import collections.abc as ca
import operator
import re
from typing import Optional

import cirq
from cirq import circuits, devices, ops, optimizers, protocols


GATE_MERGING_TOLERANCE = 1e-10


class IQMQubit(cirq.NamedQubit):
    """NamedQubit that also has a unique integer index.

    Currently the name always depends on the index.

    Args:
        index: qubit index
    """
    def __init__(self, index: int):
        super().__init__('QB{}'.format(index))
        self.index = index

    def __repr__(self):
        return 'IQMQubit({})'.format(self.index)


def _verify_unique_measurement_keys(operations: ca.Iterable[cirq.Operation]) -> None:
    """Raises an error if a measurement key is repeated in the given set of Operations.
    """
    seen_keys: set[str] = set()
    for op in operations:
        if protocols.is_measurement(op):
            key = protocols.measurement_key(op)
            if key in seen_keys:
                raise ValueError('Measurement key {} repeated'.format(key))
            seen_keys.add(key)


class IQMDevice(devices.Device):
    """ABC for the properties of a specific IQM quantum architecture.

    Adds extra functionality on top of the basic :class:`cirq.Device` class for decomposing gates,
    optimizing circuits and mapping qubits.
    """

    CONNECTIVITY: tuple[set[int]] = ()
    """qubit connectivity graph of the device"""

    NATIVE_GATES: tuple[type[cirq.Gate]] = ()
    """native gate set of the device (gate families)"""

    NATIVE_GATE_INSTANCES: tuple[cirq.Gate] = ()
    """native gate set of the device (individual gates)"""

    DECOMPOSE_FINALLY: tuple[type[cirq.Gate]] = ()
    """non-native gates that should not be decomposed when inserted into the circuit
    (we decompose them later, during the final circuit optimization stage)"""

    def __init__(self):
        # qubit set (assumes no unconnected qubits)
        qubits = {q for c in self.CONNECTIVITY for q in c}
        bad = {q for q in qubits if q < 1}
        if bad:
            raise ValueError('{} connectivity map: the qubit numbers {} are < 1.'.format(self.__class__.__name__, bad))

        expected = range(1, max(qubits) + 1)
        missing = sorted(set(expected) - qubits)
        if missing:
            raise ValueError('{} connectivity map: the qubits {} are missing.'.format(self.__class__.__name__, missing))

        self.qubits = tuple(IQMQubit(k) for k in expected)

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

    @classmethod
    def is_native_or_final(cls, op: cirq.Operation) -> bool:
        """Predicate, True iff the given operation should not be decomposed when inserted into the circuit."""
        return (
            isinstance(op, (ops.GateOperation, ops.TaggedOperation))
            and (
                isinstance(op.gate, (cls.NATIVE_GATES, cls.DECOMPOSE_FINALLY))
                or op.gate in cls.NATIVE_GATE_INSTANCES
            )
        )

    def map_circuit(self, circuit: cirq.Circuit, *, map_qubits: bool = True) -> cirq.Circuit:
        """Map the given circuit into a form that can be executed on the device.

        * Maps qubits used in the circuit to qubits used by the device.
        * Decomposes all the gates in the circuit into the native gateset.

        Args:
            circuit (cirq.Circuit): circuit to map
            map_qubits (bool): iff True, map the qubits to device qubits

        Returns:
            cirq.Circuit: mapped circuit
        """
        # TODO permute circuit qubits to try to satisfy the device connectivity
        def map_qubit(qubit: cirq.ops.Qid) -> cirq.ops.Qid:
            """NamedQubits are mapped to device qubits, other types of qubits are passed through as is."""
            if isinstance(qubit, cirq.NamedQubit):
                idx = int(re.search(r'\D*(\d+)?\D*', qubit.name).group(1))
                return self.qubits[idx - 1]
            return qubit

        def map_op(op: cirq.Operation) -> cirq.Operation:
            """Replaces the qubits the gate is acting on with corresponding device qubits."""
            qubits = map(map_qubit, op.qubits)
            return op.gate.on(*qubits)

        # map the qubits in the circuit to device qubits
        mapping = map_op if map_qubits else lambda x: x
        operations = [mapping(op) for moment in circuit.moments for op in moment.operations]

        # we need to append individual Operations (instead of Moments) to the new Circuit,
        # otherwise no decomposition is done!
        circuit = cirq.Circuit(operations, device=self)
        # The operations are immediately validated as they are appended,
        # and non-native operations decomposed by :meth:`IQMDevice.decompose_operation`.
        # There is no separate validation pass once the circuit is complete.
        return circuit

    @abc.abstractmethod
    def operation_decomposer(self, op: cirq.Operation) -> Optional[list[cirq.Operation]]:
        """Decomposes operations into the native operation set.

        Operations are decomposed immediately when they are inserted into the Circuit.
        This happens both during the Circuit creation step in :meth:`IQMDevice.map_circuit`,
        and the various point optimization rounds in :meth:`IQMDevice.simplify_circuit`.

        Args:
            op: operation to decompose

        Returns:
            decomposition, or None to pass ``op`` to the Cirq native decomposition machinery instead
        """

    def operation_final_decomposer(self, op: cirq.Operation) -> list[cirq.Operation]:
        """Decomposes all the DECOMPOSE_FINALLY operations into the native operation set.

        Called at the end of the :meth:`IQMDevice.simplify_circuit` by :class:`DecomposeGatesFinal`,
        to optionally perform one more round of decompositions.

        Args:
            op: operation to decompose

        Returns:
            decomposition (or just ``[op]``, if no decomposition is needed)
        """
        raise NotImplementedError('Decomposition missing: {}'.format(op.gate))

    def decompose_operation_full(self, op: cirq.Operation) -> cirq.OP_TREE:
        """Decomposes an operation into the native operation set.

        Args:
            op: operation to decompose

        Returns:
            decomposition (or just ``[op]``, if no decomposition is needed)

        :meth:`decompose_operation` is called automatically by Cirq whenever new gates are appended
        into the circuit. It will not decompose "final" gates, i.e. nonnative gates that should
        only be decomposed at the end of the optimization process.

        This method is like :meth:`decompose_operation`, except it additionally uses
        :meth:`operation_final_decomposer` to decompose "final" gates.
        It should be used if a full decomposition is required.
        """
        # first do the circuit insertion decomposition
        insert_dec = self.decompose_operation(op)
        if not isinstance(insert_dec, ca.Sequence):
            # the Cirq decomposition machinery may return just a naked Operation
            insert_dec = [insert_dec]

        # and then the final decomposition
        full_dec = []
        for k in insert_dec:
            if isinstance(k.gate, self.DECOMPOSE_FINALLY):
                full_dec.extend(self.operation_final_decomposer(k))
            else:
                full_dec.append(k)
        return full_dec

    def decompose_operation(self, operation: cirq.Operation) -> cirq.OP_TREE:
        if self.is_native_or_final(operation):
            return operation

        return protocols.decompose(
            operation,
            intercepting_decomposer=self.operation_decomposer,
            keep=self.is_native_or_final,
            on_stuck_raise=None
        )

    @staticmethod
    def simplify_circuit(circuit: cirq.Circuit) -> None:
        """Simplifies and optimizes the given circuit (in place).

        Args:
            circuit (cirq.Circuit): Circuit to simplify. Modified.

        Currently it

        * merges any neighboring gates belonging to the same one-parameter family
        * merges all one-qubit rotations into phased X rotations followed by Z rotations
        * pushes the Z rotations towards the end of the circuit as far as possible
        * drops any empty Moments
        """
        # the optimizers cause the immediate decomposition of any gates they insert into the Circuit
        for _ in range(7):
            # FIXME This sucks, but it seems that Cirq optimizers have no way of communicating
            # if they actually made any changes to the Circuit, so we run a fixed number of iterations.
            # Ideally we would keep doing this until the circuit hits a fixed point and no further changes are made.
            # See https://github.com/quantumlib/Cirq/issues/3761
            # all mergeable 2-qubit gates are merged
            MergeOneParameterGroupGates().optimize_circuit(circuit)
            optimizers.merge_single_qubit_gates_into_phased_x_z(circuit)
            # all z rotations are pushed past the first two-qubit gate following them
            optimizers.EjectZ(eject_parameterized=True).optimize_circuit(circuit)
            optimizers.DropEmptyMoments().optimize_circuit(circuit)

        DropRZBeforeMeasurement().optimize_circuit(circuit)
        optimizers.DropEmptyMoments().optimize_circuit(circuit)
        DecomposeGatesFinal().optimize_circuit(circuit)

    def validate_circuit(self, circuit: cirq.Circuit) -> None:
        super().validate_circuit(circuit)
        _verify_unique_measurement_keys(circuit.all_operations())

    def validate_operation(self, operation: cirq.Operation) -> None:
        if not isinstance(operation.untagged, cirq.GateOperation):
            raise ValueError('Unsupported operation: {!r}'.format(operation))

        if not self.is_native_or_final(operation):
            raise ValueError('Unsupported gate type: {!r}'.format(operation.gate))

        for qubit in operation.qubits:
            if qubit not in self.qubits:
                raise ValueError('Qubit not on device: {!r}'.format(qubit))

        self.check_qubit_connectivity(operation)

    @classmethod
    def check_qubit_connectivity(cls, operation: cirq.Operation) -> None:
        """Raises a ValueError if operation acts on qubits that are not connected.
        """
        if len(operation.qubits) >= 2 and not isinstance(operation.gate, ops.MeasurementGate):
            connection = set(q.index for q in operation.qubits)
            if connection not in cls.CONNECTIVITY:
                raise ValueError('Unsupported qubit connectivity required for {!r}'.format(operation))


class MergeOneParameterGroupGates(circuits.PointOptimizer):
    """Merges adjacent gates belonging to the same parametrized gate family.

    The merged gates have to act on the same sequence of qubits.
    This optimizer only works with gate families that are known to be one-parameter groups.

    For now, all the families are assumed to be periodic with a period of 4.
    """
    # TODO: ZZPowGate has a period of 2
    ONE_PARAMETER_FAMILIES = (ops.ISwapPowGate, ops.ZZPowGate)
    PERIOD = 4

    @classmethod
    def _normalize_par(cls, par):
        """Normalizes the given parameter value to (-period/2, period/2].
        """
        shift = cls.PERIOD / 2
        return operator.mod(par - shift, -cls.PERIOD) + shift

    def optimization_at(
            self,
            circuit: cirq.Circuit,
            index: int,
            op: cirq.Operation,
    ) -> Optional[cirq.PointOptimizationSummary]:
        """TODO the parent class at Cirq has a broken docstring here, which we have to override.
        https://github.com/quantumlib/Cirq/issues/4276
        """
        if not isinstance(op.gate, self.ONE_PARAMETER_FAMILIES):
            return None

        def is_not_mergable(next_op: cirq.Operation) -> bool:
            """Predicate for finding gates that can be merged with op.

            A gate is mergable with op iff it (1) belongs to the same gate family,
            and (2) is acting on the same qubits.
            """
            if not isinstance(next_op.gate, type(op.gate)):
                return True
            if isinstance(op.gate, ops.gate_features.InterchangeableQubitsGate):
                # same qubits in any order
                return set(op.qubits) != set(next_op.qubits)
            # same qubits in the same order
            return op.qubits != next_op.qubits

        # start searching from op onwards
        start_frontier = {q: index for q in op.qubits}
        op_list = circuit.findall_operations_until_blocked(start_frontier, is_blocker=is_not_mergable)

        if len(op_list) == 1:
            return None  # just the one gate found, no changes
        indices, operations = zip(*op_list)

        # all the gates are in the same family so we may simply sum their parameters (mod periodicity)
        par = sum(o.gate.exponent for o in operations)
        # zero parameter (mod period) corresponds to identity
        # due to floating point errors we may be just a little below the period, which should also be
        # considered close to zero so let's shift away from the troublesome point before taking the modulo
        par = self._normalize_par(par)
        if abs(par) <= GATE_MERGING_TOLERANCE:
            rewritten = []
        else:
            rewritten = op.gate.__class__(exponent=par).on(*op.qubits)

        return circuits.PointOptimizationSummary(
            clear_span=max(indices) + 1 - index,
            clear_qubits=op.qubits,
            new_operations=rewritten
        )


class DropRZBeforeMeasurement(circuits.PointOptimizer):
    """Drops z rotations that happen right before a z-basis measurement.

    These z rotations do not affect the result of the measurement, so we may ignore them.
    """
    def optimization_at(
            self,
            circuit: cirq.Circuit,
            index: int,
            op: cirq.Operation,
    ) -> Optional[cirq.PointOptimizationSummary]:
        """TODO the parent class at Cirq has a broken docstring here, which we have to override.
        https://github.com/quantumlib/Cirq/issues/4276
        """

        def find_removable_rz() -> list[int]:
            """Finds z rotations that can be removed.

            A z rotation is removable iff it is followed by a z-basis measurement.

            Returns:
                moment indices of the z rotations to be removed
            """
            remove_indices = []
            for idx, moment in enumerate(circuit[index:], start=index):
                for x in moment.operations:
                    if x.qubits == op.qubits:
                        if isinstance(x.gate, cirq.ZPowGate):  # add idx to the list, keep looking for more
                            remove_indices.append(idx)
                            break
                        if isinstance(x.gate, cirq.MeasurementGate):  # remove the accumulated indices
                            return remove_indices
                        return []  # other operations: do not remove anything
            return []  # circuit ends here: do not remove anything

        indices = find_removable_rz()
        if not indices:
            return None
        return circuits.PointOptimizationSummary(
            clear_span=max(indices) + 1 - index,
            clear_qubits=op.qubits,
            new_operations=[]
        )


class DecomposeGatesFinal(circuits.PointOptimizer):
    """Decomposes gates during the final decomposition round.
    """
    def optimization_at(
            self,
            circuit: cirq.Circuit,
            index: int,
            op: cirq.Operation,
    ) -> Optional[cirq.PointOptimizationSummary]:
        """TODO the parent class at Cirq has a broken docstring here, which we have to override.
        https://github.com/quantumlib/Cirq/issues/4276
        """
        if not isinstance(op.gate, circuit.device.DECOMPOSE_FINALLY):
            return None  # no changes

        rewritten = circuit.device.operation_final_decomposer(op)
        return circuits.PointOptimizationSummary(
            clear_span=1,
            clear_qubits=op.qubits,
            new_operations=rewritten
        )
