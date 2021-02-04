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
from cirq import ops

import cirq_iqm.iqm_device as idev
import cirq_iqm.iqm_gates as ig


class Adonis(idev.IQMDevice):
    """IQM's five-qubit transmon device.

    The qubits are connected thus::

            QB1
             |
      QB2 - QB3 - QB4
             |
            QB5

    where the lines denote which qubit pairs can be subject to two-qubit gates.

    Each qubit can be rotated about the x, y, and z axes by an arbitrary angle, i.e. Adonis has native XPowGate,
    YPowGate, and ZPowGate gates. The native two qubit gates are IsingGate and XYGate, each accepting a real
    scalar parameter ("exponent" in Cirq terminology).
    The qubits can be measured simultaneously or separately at any time.
    """

    CONNECTIVITY = ({1, 3}, {2, 3}, {4, 3}, {5, 3})

    # Subject to change
    NATIVE_GATES = (
        ops.PhasedXPowGate,
        ops.XPowGate,
        ops.YPowGate,
        ops.ZPowGate,
        ig.IsingGate,
        ig.XYGate,
        ops.MeasurementGate
    )

    def operation_decomposer(self, op):
        """Decomposes gates into the native Adonis gate set.

        For now provides a special decomposition for CZPowGate only, which seems to be enough.
        """
        if isinstance(op.gate, ops.CZPowGate):
            # decompose CZPowGate using IsingGate
            s = 1 - op.gate.exponent / 2
            G = ig.IsingGate(exponent=s)
            # local Z rotations
            L = ops.ZPowGate(exponent=-s)
            return [G.on(*op.qubits), L.on(op.qubits[0]), L.on(op.qubits[1])]
        if isinstance(op.gate, ops.ISwapPowGate):
            # the ISwap family is implemented using the XY interaction
            return [ig.XYGate(exponent=-0.5 * op.gate.exponent).on(*op.qubits)]
        return None
