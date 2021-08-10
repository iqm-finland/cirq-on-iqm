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
from typing import Optional, Union

import cirq
from cirq import circuits, devices, ops, optimizers, protocols
from cirq.contrib.routing.router import route_circuit, nx


GATE_MERGING_TOLERANCE = 1e-10

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

    DECOMPOSE_FINALLY: tuple[type[cirq.Gate]] = ()
    """non-native gates that should not be decomposed when inserted into the circuit
    (we decompose them later, during the final circuit optimization stage)"""

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

    @abc.abstractmethod
    def operation_decomposer(self, op: cirq.Operation) -> Optional[list[cirq.Operation]]:
        """Decomposes operations into the native operation set.

        Operations are decomposed immediately when they are inserted into a Circuit associated with an IQMDevice.
        This happens at various points during the optimization rounds in :meth:`IQMDevice.simplify_circuit`.

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
        raise NotImplementedError(f'Decomposition missing: {op.gate}')

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

    def simplify_circuit(self, circuit: cirq.Circuit, max_iterations: int = 20) -> None:
        """Simplifies and optimizes the given circuit.

        Currently it

        * merges any neighboring gates belonging to the same one-parameter family
        * merges all one-qubit rotations into phased X rotations followed by Z rotations
        * pushes the Z rotations towards the end of the circuit as far as possible
        * drops any empty Moments

        This sequence of optimization passes is repeated until the circuit hits a fixed point,
        or ``max_iterations`` is exceeded.

        Finally, it removes Z rotations that are immediately followed by a Z-basis measurement,
        and runs :meth:`operation_final_decomposer` on the circuit.

        Args:
            circuit: circuit to simplify
            max_iterations: maximum number of simplification rounds

        Returns:
            simplified circuit
        """
        c = circuit.copy()

        # the optimizers cause the immediate decomposition of any gates they insert into the Circuit
        for _ in range(max_iterations):
            # It seems that Cirq optimizers have no way of communicating
            # if they actually made any changes to the Circuit.
            # See https://github.com/quantumlib/Cirq/issues/3761

            before = c.copy()

            # all mergeable 2-qubit gates are merged
            MergeOneParameterGroupGates().optimize_circuit(c)
            optimizers.merge_single_qubit_gates_into_phased_x_z(c)
            # all z rotations are pushed past the first two-qubit gate following them
            optimizers.EjectZ(eject_parameterized=True).optimize_circuit(c)
            optimizers.DropEmptyMoments().optimize_circuit(c)

            if c == before:
                # the optimization hit a fixed point
                break

        DropRZBeforeMeasurement().optimize_circuit(c)
        optimizers.DropEmptyMoments().optimize_circuit(c)
        DecomposeGatesFinal(self).optimize_circuit(c)
        return c

    def validate_circuit(self, circuit: cirq.Circuit) -> None:
        super().validate_circuit(circuit)
        _verify_unique_measurement_keys(circuit.all_operations())

    def validate_operation(self, operation: cirq.Operation) -> None:
        if not isinstance(operation.untagged, cirq.GateOperation):
            raise ValueError(f'Unsupported operation: {operation!r}')

        if not self.is_native_or_final(operation):
            raise ValueError(f'Unsupported gate type: {operation.gate!r}')

        for qubit in operation.qubits:
            if qubit not in self.qubits:
                raise ValueError(f'Qubit not on device: {qubit!r}')

        self.check_qubit_connectivity(operation)


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
        """Describes how to change operations near the given location.

        Args:
            circuit: The circuit to improve.
            index: The index of the moment with the operation to focus on.
            op: The operation to focus improvements upon.

        Returns:
            A description of the optimization to perform, or else None if no
            change should be made.
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
        """Describes how to change operations near the given location.

        Args:
            circuit: The circuit to improve.
            index: The index of the moment with the operation to focus on.
            op: The operation to focus improvements upon.

        Returns:
            A description of the optimization to perform, or else None if no
            change should be made.
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
                    if isinstance(x.gate, cirq.ZPowGate) and x.qubits == op.qubits:
                        # add idx to the list, keep looking for more
                        remove_indices.append(idx)
                        break  # to next moment
                    if isinstance(x.gate, cirq.MeasurementGate) and op.qubits[0] in x.qubits:
                        # follows the ZPowGates, remove the accumulated indices
                        return remove_indices
                    return []  # other operations: do not remove anything
            return []  # circuit ends here: do not remove anything

        if not isinstance(op.gate, cirq.ZPowGate):
            return None  # shortcut
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
    def __init__(self, device: IQMDevice):
        """
        Args:
            device: device whose :meth:`.IQMDevice.operation_final_decomposer` to use
        """
        super().__init__()
        self.device = device

    def optimization_at(
            self,
            circuit: cirq.Circuit,
            index: int,
            op: cirq.Operation,
    ) -> Optional[cirq.PointOptimizationSummary]:
        """Describes how to change operations near the given location.

        Args:
            circuit: The circuit to improve.
            index: The index of the moment with the operation to focus on.
            op: The operation to focus improvements upon.

        Returns:
            A description of the optimization to perform, or else None if no
            change should be made.
        """
        if not isinstance(op.gate, self.device.DECOMPOSE_FINALLY):
            return None  # no changes

        rewritten = self.device.operation_final_decomposer(op)
        return circuits.PointOptimizationSummary(
            clear_span=1,
            clear_qubits=op.qubits,
            new_operations=rewritten
        )
