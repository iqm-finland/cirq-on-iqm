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
IQM's Valkmusa quantum architecture.
"""
from math import pi as PI
from typing import Optional

import cirq
from cirq import ops

from .iqm_device import IQMDevice, IQMDeviceMetadata

PI_2 = PI / 2

# common gates used in gate decompositions
Lx = ops.rx(PI_2)
Lxi = ops.rx(-PI_2)
Ly = ops.ry(PI_2)
Lyi = ops.ry(-PI_2)
Lz = ops.rz(PI_2)
Lzi = ops.rz(-PI_2)


class Valkmusa(IQMDevice):
    """IQM's two-qubit transmon device.

    The qubits are connected thus::

      QB1 - QB2

    Each qubit can be rotated about any axis in the xy plane by an arbitrary angle.
    The native two qubit-gate is ISwapPowGate.
    The qubits are always measured simultaneously at the end of the computation.
    """

    def __init__(self):
        qubit_count = 2
        connectivity = ({1, 2},)
        gateset = cirq.Gateset(
            ops.PhasedXPowGate,
            # XPow and YPow kept for convenience, Cirq does not know how to decompose them into PhasedX
            # so we would have to add those rules...
            ops.XPowGate,
            ops.YPowGate,
            ops.ISwapPowGate,
            ops.MeasurementGate,
        )
        super().__init__(IQMDeviceMetadata.from_qubit_indices(qubit_count, connectivity, gateset))

    def operation_decomposer(self, op: ops.Operation) -> Optional[list[ops.Operation]]:
        # Decomposes CNOT and the CZPowGate family to Valkmusa native gates.
        # All the decompositions below keep track of global phase (required for decomposing controlled gates).

        if isinstance(op.gate, ops.CXPowGate) and op.gate.exponent == 1.0:
            # CNOT is a special case, we decompose it using iSWAPs to be able to commute Z rotations through
            control_qubit = op.qubits[0]
            target_qubit = op.qubits[1]
            s = op.gate.global_shift
            iSWAP = ops.ISwapPowGate(exponent=1, global_shift=(s + 0.25) / 2)
            return [
                Lx.on(target_qubit),
                Lzi.on(control_qubit),
                Lz.on(target_qubit),
                iSWAP.on(*op.qubits),
                Lx.on(control_qubit),
                iSWAP.on(*op.qubits),
                Lz.on(target_qubit),
            ]
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
            # ZZPowGate is decomposed using two applications of the XY interaction
            t = op.gate.exponent
            s = op.gate.global_shift
            XY = ops.ISwapPowGate(exponent=-t, global_shift=-(s + 0.5) / 2)
            return [
                Lyi.on(op.qubits[0]),
                Lyi.on(op.qubits[1]),
                XY.on(*op.qubits),
                ops.XPowGate(exponent=-1, global_shift=-0.5).on(op.qubits[0]),
                XY.on(*op.qubits),
                ops.XPowGate(exponent=1, global_shift=-0.5).on(op.qubits[0]),
                Ly.on(op.qubits[0]),
                Ly.on(op.qubits[1]),
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
