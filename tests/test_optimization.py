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

import cirq
from cirq import ops
import pytest

from cirq_iqm.optimizers import DropRZBeforeMeasurement, MergeOneParameterGroupGates, simplify_circuit

TOLERANCE = 1e-10  # numerical tolerance


@pytest.fixture(scope='module')
def qubits():
    return [cirq.NamedQubit('Alice'), cirq.NamedQubit('Bob'), cirq.NamedQubit('Charlie')]


class TestGateOptimization:
    """Test various circuit optimization techniques."""

    @pytest.mark.parametrize(
        'family',
        [
            ops.ZZPowGate,
            ops.ISwapPowGate,
        ],
    )
    @pytest.mark.parametrize('a, b', [(0, 0.3), (-0.5, 0.5), (1.0, 2.0), (0.1, -4.1)])
    def test_gate_merging(self, family, a, b, qubits):
        """Merging one-parameter group gates."""

        q0, q1 = qubits[:2]

        c = cirq.Circuit()
        c.append(
            [
                family(exponent=a)(q0, q1),
                family(exponent=b)(q0, q1),
            ]
        )

        MergeOneParameterGroupGates().optimize_circuit(c)
        c = cirq.drop_empty_moments(c)

        if abs((a + b) % MergeOneParameterGroupGates.PERIOD) < 1e-10:
            # the gates have canceled each other out
            assert len(c) == 0
        else:
            # the gates have been merged
            assert len(c) == 1
            expected = MergeOneParameterGroupGates._normalize_par(a + b)
            assert c[0].operations[0].gate.exponent == pytest.approx(expected, abs=TOLERANCE)

    @pytest.mark.parametrize(
        'family, ex',
        [
            (cirq.ops.CZPowGate, 0.2),  # diagonal
            (ops.ISwapPowGate, 1),  # swaplike with Rz when ex is an odd integer
            (ops.ISwapPowGate, 3),
            pytest.param(ops.ISwapPowGate, 0.6, marks=pytest.mark.xfail(strict=True)),
            # diagonal, but currently do not work with EjectZ
            pytest.param(
                ops.ZZPowGate, 0.37, marks=pytest.mark.xfail(strict=True, reason='Implementation missing in Cirq.')
            ),
            pytest.param(
                ops.ISwapPowGate, 2, marks=pytest.mark.xfail(strict=True, reason='Implementation missing in Cirq.')
            ),
        ],
    )
    def test_eject_z(self, family, ex, qubits):
        """Commuting z rotations towards the end of the circuit."""

        q0, q1 = qubits[:2]

        c = cirq.Circuit()
        c.append(
            [
                cirq.ZPowGate(exponent=0.3)(q0),
                cirq.ZPowGate(exponent=0.8)(q1),
                family(exponent=ex)(q0, q1),
                cirq.MeasurementGate(1, key='q0')(q0),
                cirq.MeasurementGate(1, key='q1')(q1),
            ]
        )

        c = cirq.eject_z(c)
        c = cirq.drop_empty_moments(c)

        # the ZPowGates have been commuted and canceled
        assert len(c) == 2


class TestSimplifyCircuit:
    @pytest.mark.parametrize(
        'two_qubit_gate',
        [
            cirq.CZPowGate(exponent=1),
            pytest.param(
                cirq.ZZPowGate(exponent=0.1),
                marks=pytest.mark.xfail(
                    strict=True,
                    reason='ZZPowGate does not yet implement the _phase_by_ protocol in Cirq.',
                    raises=AssertionError,
                ),
            ),
        ],
    )
    def test_simplify_circuit_eject_z(self, two_qubit_gate, qubits):

        q0, q1 = qubits[:2]
        c = cirq.Circuit()
        c.append(
            [
                cirq.ZPowGate(exponent=0.55)(q0),
                two_qubit_gate(q0, q1),
                cirq.MeasurementGate(2, key='mk')(q0, q1),
            ]
        )
        new = simplify_circuit(c)

        assert len(new) == 2

    def test_simplify_circuit_merge_one_parameter_gates(self, qubits):

        q0, q1 = qubits[:2]
        c = cirq.Circuit()
        c.append(
            [
                cirq.ZZPowGate(exponent=0.3)(q0, q1),
                cirq.ZZPowGate(exponent=0.1)(q0, q1),
            ]
        )
        new = simplify_circuit(c)

        # ZZPowGates have been merged
        assert len(new) == 1

    def test_simplify_circuit_drop_rz_before_measurement(self, qubits):

        q0, q1 = qubits[:2]
        c = cirq.Circuit()
        c.append(
            [
                cirq.ZPowGate(exponent=0.1)(q0),
                cirq.ZPowGate(exponent=0.2)(q1),
                cirq.MeasurementGate(1, key='measurement')(q0),
            ]
        )
        new = simplify_circuit(c)

        # the ZPowGate preceding the measurement has been dropped
        assert len(new) == 2
        assert isinstance(new[0].operations[0].gate, cirq.ZPowGate)
        assert new[0].operations[0].qubits == (q1,)

    def test_drop_rz_before_measurement(self, qubits):

        q0, q1, q2 = qubits[:3]
        c = cirq.Circuit()
        c.append(
            [
                (cirq.X**0.4)(q0),
                cirq.ZPowGate(exponent=0.1)(q1),
                cirq.MeasurementGate(1, key='measurement')(q1),
                cirq.ZPowGate(exponent=0.2)(q2),
            ]
        )
        new = c.copy()
        DropRZBeforeMeasurement().optimize_circuit(new)

        assert len(new) == 2  # still 2 Moments
        # the ZPowGate preceding the measurement has been dropped
        assert len(tuple(new.all_operations())) == 3
        op = new[0].operations[0]
        assert isinstance(op.gate, cirq.XPowGate)
        assert op.qubits == (q0,)
        op = new[0].operations[1]
        assert isinstance(op.gate, cirq.ZPowGate)
        assert op.qubits == (q2,)

    def test_drop_rz_before_measurement_drop_final(self, qubits):

        q0, q1, q2 = qubits[:3]
        c = cirq.Circuit()
        c.append(
            [
                (cirq.X**0.4)(q0),
                cirq.ZPowGate(exponent=0.1)(q1),  # Rz followed by measurement
                cirq.MeasurementGate(1, key='measurement')(q1),
                cirq.ZPowGate(exponent=0.2)(q2),  # final Rz
            ]
        )
        new = c.copy()
        DropRZBeforeMeasurement(drop_final=True).optimize_circuit(new)

        assert len(new) == 2  # still 2 Moments
        # both ZPowGates were dropped
        assert len(tuple(new.all_operations())) == 2
        op = new[0].operations[0]
        assert isinstance(op.gate, cirq.XPowGate)
        assert op.qubits == (q0,)

    def test_simplify_circuit_merge_one_qubit_gates(self, qubits):

        q0 = qubits[0]
        c = cirq.Circuit()
        c.append(
            [
                cirq.XPowGate(exponent=0.1)(q0),
                cirq.YPowGate(exponent=0.2)(q0),
                cirq.ZPowGate(exponent=0.3)(q0),
            ]
        )
        new = simplify_circuit(c)

        # the one-qubit gates have been merged
        assert len(new) == 2
        assert isinstance(new[0].operations[0].gate, cirq.PhasedXPowGate)
        assert isinstance(new[1].operations[0].gate, cirq.ZPowGate)
