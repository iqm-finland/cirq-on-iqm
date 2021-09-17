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

from math import pi as PI
from typing import Optional

import cirq
from cirq import ops

from .iqm_device import IQMDevice

PI_2 = PI / 2

# common gates used in gate decompositions
CZ = ops.CZPowGate()
Lx = ops.rx(PI_2)
Lxi = ops.rx(-PI_2)
Ly = ops.ry(PI_2)
Lyi = ops.ry(-PI_2)


class Adonis(IQMDevice):
    """IQM's five-qubit transmon device.

    The qubits are connected thus::

            QB1
             |
      QB2 - QB3 - QB4
             |
            QB5

    where the lines denote which qubit pairs can be subject to two-qubit gates.

    Each qubit can be rotated about any axis in the xy plane by an arbitrary angle.
    Adonis thus has native PhasedXPowGate, XPowGate, and YPowGate gates. The two-qubit gate CZ is
    native, as well. The qubits can be measured simultaneously or separately once, at the end of
    the circuit.
    """

    QUBIT_COUNT = 5

    CONNECTIVITY = ({1, 3}, {2, 3}, {4, 3}, {5, 3})

    NATIVE_GATES = (
        ops.PhasedXPowGate,
        ops.XPowGate,
        ops.YPowGate,
        ops.MeasurementGate
    )

    NATIVE_GATE_INSTANCES = (
        ops.CZPowGate(),
    )

    def operation_decomposer(self, op: cirq.Operation) -> Optional[list[cirq.Operation]]:
        # Decomposes gates into the native Adonis gate set.
        # All the decompositions below keep track of global phase (required for decomposing controlled gates).
        # It seems that Cirq native decompositions ignore global phase entirely?

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
                ops.XPowGate(exponent=x, global_shift=-0.5 -2 * s).on(op.qubits[0]),
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
