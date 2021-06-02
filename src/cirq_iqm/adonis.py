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
IQM's Adonis quantum architecture.
"""
from __future__ import annotations

from typing import Optional

import cirq
from cirq import ops

import cirq_iqm.iqm_device as idev
import cirq_iqm.iqm_gates as ig

# common gates used in gate decompositions
CZ = ops.CZPowGate()
Lx = ops.XPowGate(exponent=0.5, global_shift=-0.5)
Lxi = ops.XPowGate(exponent=-0.5, global_shift=-0.5)
Ly = ops.YPowGate(exponent=0.5, global_shift=-0.5)
Lyi = ops.YPowGate(exponent=-0.5, global_shift=-0.5)


class Adonis(idev.IQMDevice):
    """IQM's five-qubit transmon device.

    The qubits are connected thus::

            QB1
             |
      QB2 - QB3 - QB4
             |
            QB5

    where the lines denote which qubit pairs can be subject to two-qubit gates.

    Each qubit can be rotated about any axis in the xy plane, or the z axis, by an arbitrary angle.
    Adonis thus has native PhasedXPowGate, XPowGate, YPowGate, and ZPowGate gates.
    The only native two qubit gate is CZ.
    The qubits can be measured simultaneously or separately once, at the end of the circuit.
    """

    CONNECTIVITY = ({1, 3}, {2, 3}, {4, 3}, {5, 3})

    # Subject to change
    NATIVE_GATES = (
        ops.PhasedXPowGate,
        ops.XPowGate,
        ops.YPowGate,
        ops.ZPowGate,
        ops.MeasurementGate
    )

    NATIVE_GATE_INSTANCES = (
        ops.CZPowGate(),
    )

    def operation_decomposer(self, op: cirq.Operation) -> Optional[list[cirq.Operation]]:
        """Decomposes gates into the native Adonis gate set.
        """
        # NOTE: All the decompositions below keep track of global phase (required for decomposing
        # controlled gates), but for now assume that op.gate.global_shift is zero.
        # It seems that Cirq native decompositions ignore global phase entirely.

        if isinstance(op.gate, ops.ISwapPowGate):
            # the ISwap family is implemented using the XY interaction
            s = -0.5 * op.gate.exponent
            return [
                ig.XYGate(exponent=s).on(*op.qubits)
            ]
        if isinstance(op.gate, ops.CZPowGate):
            # decompose CZPowGate using IsingGate
            s = -0.5 * op.gate.exponent
            L = ops.ZPowGate(exponent=-s, global_shift=-0.5)
            return [
                ig.IsingGate(exponent=s, global_shift=-0.5).on(*op.qubits),
                L.on(op.qubits[0]),
                L.on(op.qubits[1]),
            ]
        if isinstance(op.gate, ig.IsingGate):
            # decompose IsingGate using two CZs
            s = op.gate.exponent
            return [
                Lyi.on(op.qubits[1]),
                CZ.on(*op.qubits),
                ops.XPowGate(exponent=-s, global_shift=-0.5).on(op.qubits[1]),
                CZ.on(*op.qubits),
                Ly.on(op.qubits[1]),
            ]
        if isinstance(op.gate, ig.XYGate):
            # decompose XYGate using two CZs
            s = op.gate.exponent
            return [
                Lxi.on(op.qubits[0]),
                Lxi.on(op.qubits[1]),
                Lyi.on(op.qubits[1]),
                CZ.on(*op.qubits),
                ops.XPowGate(exponent=s, global_shift=-0.5).on(op.qubits[0]),
                ops.XPowGate(exponent=-s, global_shift=-0.5).on(op.qubits[1]),
                CZ.on(*op.qubits),
                Ly.on(op.qubits[1]),
                Lx.on(op.qubits[0]),
                Lx.on(op.qubits[1]),
            ]
        return None
