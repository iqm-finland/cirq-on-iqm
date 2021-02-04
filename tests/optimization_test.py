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

"""Tests for the circuit optimization passes.
"""
# pylint: disable=no-self-use
import pytest
import cirq

import cirq_iqm.iqm_gates as ig
from cirq_iqm.iqm_device import MergeOneParameterGroupGates, IQMEjectZ


tol = 1e-10  # numerical tolerance


class TestGateOptimization:
    """Test various circuit optimization techniques."""

    @pytest.mark.parametrize('family', [
        ig.IsingGate,
        ig.XYGate,
    ])
    @pytest.mark.parametrize('a, b', [(0, 0.3), (-0.5, 0.5), (0.3, 1.7), (0.1, -4.1)])
    def test_gate_merging(self, family, a, b):
        """Merging one-parameter group gates."""

        q0, q1 = cirq.NamedQubit('q0'), cirq.NamedQubit('q1')

        c = cirq.Circuit()
        c.append([
            family(exponent=a)(q0, q1),
            family(exponent=b)(q0, q1),
        ])

        MergeOneParameterGroupGates().optimize_circuit(c)
        cirq.optimizers.DropEmptyMoments().optimize_circuit(c)

        if abs((a + b) % 2) < 1e-10:
            # the gates have canceled each other out
            assert len(c) == 0
        else:
            # the gates have been merged
            assert len(c) == 1
            assert c[0].operations[0].gate.exponent == pytest.approx(a + b, abs=tol)


    @pytest.mark.parametrize('family, ex', [
        (ig.IsingGate, 0.37),  # always commutes with Rz
        (ig.XYGate, 0.5),  # is swaplike with Rz only when ex is int+0.5
        (ig.XYGate, 1.5),
        pytest.param(ig.XYGate, 0.3, marks=pytest.mark.xfail(strict=True)),
        (cirq.ops.CZPowGate, 0.2),
    ])
    def test_eject_z(self, family, ex):
        """Commuting z rotations towards the end of the circuit."""

        q0, q1 = cirq.NamedQubit('q0'), cirq.NamedQubit('q1')

        c = cirq.Circuit()
        c.append([
            cirq.ZPowGate(exponent=0.3)(q0),
            cirq.ZPowGate(exponent=0.8)(q1),
            family(exponent=ex)(q0, q1),
            cirq.MeasurementGate(1)(q0),
            cirq.MeasurementGate(1)(q1),
        ])

        IQMEjectZ().optimize_circuit(c)
        cirq.optimizers.DropEmptyMoments().optimize_circuit(c)

        # the gates have been commuted and canceled
        assert len(c) == 2
