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
Circuit optimization classes.
"""
import operator
from typing import Optional

import cirq
from cirq import circuits, ops


def simplify_circuit(
    circuit: cirq.Circuit,
    *,
    max_iterations: int = 20,
    drop_final_rz: bool = False,
) -> cirq.Circuit:
    """Simplifies and optimizes the given circuit.

    Currently it

    * merges any neighboring gates belonging to the same one-parameter family
    * merges all one-qubit rotations into phased X rotations followed by Z rotations
    * pushes the Z rotations towards the end of the circuit as far as possible
    * drops any empty Moments

    This sequence of optimization passes is repeated until the circuit hits a fixed point,
    or ``max_iterations`` is exceeded.

    Finally, it removes Z rotations that are immediately followed by a Z-basis measurement.

    Args:
        circuit: circuit to simplify
        max_iterations: maximum number of simplification rounds
        drop_final_rz: iff True, drop z rotations that have no successor operations

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
        c = cirq.merge_single_qubit_gates_to_phased_x_and_z(c)
        # all z rotations are pushed past the first two-qubit gate following them
        c = cirq.eject_z(c, eject_parameterized=True)
        c = cirq.drop_empty_moments(c)

        if c == before:
            # the optimization hit a fixed point
            break

    DropRZBeforeMeasurement(drop_final=drop_final_rz).optimize_circuit(c)
    c = cirq.drop_empty_moments(c)

    return c


class MergeOneParameterGroupGates(circuits.PointOptimizer):
    """Merges adjacent gates belonging to the same parametrized gate family.

    The merged gates have to act on the same sequence of qubits.
    This optimizer only works with gate families that are known to be one-parameter groups.

    For now, all the families are assumed to be periodic with a period of 4.
    """

    # TODO: ZZPowGate has a period of 2
    ONE_PARAMETER_FAMILIES = (ops.ISwapPowGate, ops.ZZPowGate)
    PERIOD = 4
    GATE_MERGING_TOLERANCE = 1e-10

    @classmethod
    def _normalize_par(cls, par):
        """Normalizes the given parameter value to (-period/2, period/2]."""
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
        if abs(par) <= self.GATE_MERGING_TOLERANCE:
            rewritten: 'cirq.OP_TREE' = []
        else:
            rewritten = op.gate.__class__(exponent=par).on(*op.qubits)

        return circuits.PointOptimizationSummary(
            clear_span=max(indices) + 1 - index, clear_qubits=op.qubits, new_operations=rewritten
        )


class DropRZBeforeMeasurement(circuits.PointOptimizer):
    """Drops z rotations that happen right before a z-basis measurement.

    These z rotations do not affect the result of the measurement, so we may ignore them.

    Args:
        drop_final: iff True, drop also any z rotation at the end of the circuit (since it's not
            followed by a measurement, it cannot affect them)
    """

    def __init__(self, drop_final: bool = False):
        super().__init__()
        self.drop_final = drop_final

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
            # op is a ZPowGate
            remove_indices = []
            for idx, moment in enumerate(circuit[index:], start=index):
                for x in moment.operations:
                    if op.qubits[0] in x.qubits:
                        # x acts on the same qubit as op
                        if isinstance(x.gate, cirq.ZPowGate):
                            # add idx to the list, keep looking for more
                            remove_indices.append(idx)
                            break  # to next moment
                        if isinstance(x.gate, cirq.MeasurementGate):
                            # follows the ZPowGates, remove the accumulated indices
                            return remove_indices
                        return []  # other operations: do not remove anything
            # circuit ends here
            if self.drop_final:
                return remove_indices
            return []

        if not isinstance(op.gate, cirq.ZPowGate):
            return None  # shortcut
        indices = find_removable_rz()
        if not indices:
            return None
        return circuits.PointOptimizationSummary(
            clear_span=max(indices) + 1 - index, clear_qubits=op.qubits, new_operations=[]
        )
