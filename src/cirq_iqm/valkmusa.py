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
IQM's Valkmusa quantum architecture.
"""
from cirq import ops

import cirq_iqm.iqm_device as idev
import cirq_iqm.iqm_gates as ig


class Valkmusa(idev.IQMDevice):
    """IQM's two-qubit transmon device.

    ::

      QB1 - QB2

    Each qubit can be rotated about any axis in the xy plane by an arbitrary angle.
    The native two qubit-gate is XYGate.
    The qubits are always measured simultaneously at the end of the computation.
    """

    CONNECTIVITY = ({1, 2},)

    NATIVE_GATES = (
        ops.PhasedXPowGate,
        # XPow and YPow kept for convenience, Cirq does not know how to decompose them into PhasedX
        # so we would have to add those rules...
        ops.XPowGate,
        ops.YPowGate,
        ig.XYGate,
        ops.MeasurementGate
    )

    # we postpone the decomposition of the z rotations until the final stage of optimization
    DECOMPOSE_FINALLY = (ops.ZPowGate,)

    def operation_final_decomposer(self, op: ops.Operation):
        """Decomposes z rotations using x and y rotations."""
        if isinstance(op.gate, ops.ZPowGate):
            # Rz using Rx, Ry
            q = op.qubits[0]
            return [
                ops.XPowGate(exponent=-0.5).on(q),
                ops.YPowGate(exponent=op.gate.exponent).on(q),
                ops.XPowGate(exponent=0.5).on(q),
            ]
        raise NotImplementedError('Decomposition missing: {}'.format(op.gate))

    def operation_decomposer(self, op: ops.Operation):
        """Decomposes CNOT and the CZPowGate family to Valkmusa native gates."""
        if isinstance(op.gate, ops.CXPowGate) and op.gate.exponent == 1.0:
            # CNOT is a special case, we decompose it using iSWAPs to be able to commute Z rotations through
            control_qubit = op.qubits[0]
            target_qubit = op.qubits[1]
            iSWAP = ig.XYGate(exponent=-1/2)
            return [
                ops.XPowGate(exponent=0.5).on(target_qubit),
                ops.ZPowGate(exponent=-0.5).on(control_qubit),
                ops.ZPowGate(exponent=0.5).on(target_qubit),
                iSWAP.on(*op.qubits),
                ops.XPowGate(exponent=0.5).on(control_qubit),
                iSWAP.on(*op.qubits),
                ops.ZPowGate(exponent=0.5).on(target_qubit),
            ]
        if isinstance(op.gate, ops.CZPowGate):
            # the CZ family is decomposed using two applications of the XY interaction
            s = -op.gate.exponent / 4
            r = -2 * s
            return [
                ops.XPowGate(exponent=0.5).on(op.qubits[0]),
                ops.YPowGate(exponent=-0.5).on(op.qubits[1]),
                ops.ZPowGate(exponent=0.5).on(op.qubits[1]),
                ig.XYGate(exponent=s).on(*op.qubits),
                ops.YPowGate(exponent=1).on(op.qubits[1]),
                ig.XYGate(exponent=s).on(*op.qubits),
                ops.XPowGate(exponent=-0.5).on(op.qubits[0]),
                ops.YPowGate(exponent=0.5).on(op.qubits[1]),
                ops.XPowGate(exponent=-0.5).on(op.qubits[1]),
                ops.ZPowGate(exponent=r).on(op.qubits[0]),
                ops.ZPowGate(exponent=r+1).on(op.qubits[1]),
            ]
        if isinstance(op.gate, ops.ISwapPowGate):
            # the ISwap family is implemented using the XY interaction
            return [ig.XYGate(exponent=-0.5 * op.gate.exponent).on(*op.qubits)]
        return None
