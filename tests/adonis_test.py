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

"""Tests for the Adonis device.
"""
# pylint: disable=redefined-outer-name,no-self-use,duplicate-code

from __future__ import annotations

import cirq
import numpy as np
import pytest

import cirq_iqm.adonis as ad


def dist(U: np.ndarray, W: np.ndarray) -> float:
    r"""Distance between two unitary matrices, modulo global phase.

    Returns:
        minimal squared Frobenius norm distance between the unitaries over all global phases

    .. math::
       \mathrm{dist}(U, W) = \inf_{\phi \in \mathbb{R}} \|U - e^{i \phi} W\|_F^2
       = 2 (\dim_A - |\mathrm{Tr}(U^\dagger W)|)
    """
    return 2 * (len(U) - np.abs(np.trace(U.T.conj() @ W)))


@pytest.fixture(scope='module')
def adonis():
    """Adonis device fixture."""
    return ad.Adonis()


# define various groups of gates to test

native_1q_gates = [
    cirq.X,
    cirq.Y,
    cirq.XPowGate(exponent=0.23),
    cirq.YPowGate(exponent=0.71),
    cirq.PhasedXPowGate(phase_exponent=1.7, exponent=-0.58),
    cirq.Z,
    cirq.ZPowGate(exponent=-0.23),
]

finally_decomposed_1q_gates = []

native_2q_gates = [
    cirq.CZ,
]

non_native_1q_gates = [
    cirq.H,
    cirq.HPowGate(exponent=-0.55),
    cirq.PhasedXZGate(x_exponent=0.2, z_exponent=-0.5, axis_phase_exponent=0.75),
]

non_native_2q_gates = [
    cirq.ISWAP,
    cirq.ISwapPowGate(exponent=0.27),
    cirq.SWAP,
    cirq.CNOT,
    cirq.CXPowGate(exponent=-2.2),
    cirq.CZPowGate(exponent=1.6),
    cirq.ZZPowGate(exponent=-0.94),
]


class TestOperationValidation:
    """Nativity and validation of various operations."""

    @pytest.mark.parametrize('gate', native_1q_gates)
    @pytest.mark.parametrize('q', [0, 2, 3])
    def test_native_single_qubit_gates(self, adonis, gate, q):
        """Native operations must pass validation."""

        adonis.validate_operation(gate(adonis.qubits[q]))
        adonis.validate_operation(gate(adonis.qubits[q]).with_tags('tag_foo'))

    @pytest.mark.parametrize('gate', native_2q_gates)
    def test_native_two_qubit_gates(self, adonis, gate):
        """Native operations must pass validation."""

        q0, _, q2 = adonis.qubits[:3]

        adonis.validate_operation(gate(q0, q2))
        adonis.validate_operation(gate(q2, q0))

    @pytest.mark.parametrize('meas', [
        cirq.measure,
        lambda q: cirq.measure(q, key='test'),
    ])
    def test_native_measurements(self, adonis, meas):
        """Native operations must pass validation."""

        adonis.validate_operation(meas(adonis.qubits[0]))

    @pytest.mark.parametrize('gate', non_native_1q_gates)
    def test_non_native_single_qubit_gates(self, adonis, gate):
        """Non-native operations must not pass validation."""

        q0 = adonis.qubits[0]

        with pytest.raises(ValueError, match='Unsupported gate type'):
            adonis.validate_operation(gate(q0))

        with pytest.raises(ValueError, match='Unsupported gate type'):
            adonis.validate_operation(gate(q0).with_tags('tag_foo'))

    @pytest.mark.parametrize('gate', non_native_2q_gates)
    def test_non_native_two_qubit_gates(self, adonis, gate):
        """Non-native operations must not pass validation."""

        q0, _, q2 = adonis.qubits[:3]

        with pytest.raises(ValueError, match='Unsupported gate type'):
            adonis.validate_operation(gate(q0, q2))

        with pytest.raises(ValueError, match='Unsupported gate type'):
            adonis.validate_operation(gate(q2, q0))

    @pytest.mark.parametrize('qubit', [
        cirq.NamedQubit('xxx'),
        cirq.NamedQubit('QB1'),  # name ok, but not a device qubit
        cirq.GridQubit(0, 1),
    ])
    def test_qubits_not_on_device(self, adonis, qubit):
        """Gates operating on qubits not on device must not pass validation."""

        with pytest.raises(ValueError, match='Qubit not on device'):
            adonis.validate_operation(cirq.X(qubit))

    @pytest.mark.parametrize('gate', native_2q_gates)
    def test_qubits_not_connected(self, adonis, gate):
        """Native two-qubit gates operating on non-connected qubits must not pass validation."""

        q0, q1 = adonis.qubits[:2]

        with pytest.raises(ValueError, match='Unsupported qubit connectivity'):
            adonis.validate_operation(gate(q0, q1))

        with pytest.raises(ValueError, match='Unsupported qubit connectivity'):
            adonis.validate_operation(gate(q1, q0))


class TestGateDecomposition:
    """Decomposing gates."""

    @staticmethod
    def is_native(op_or_op_list) -> bool:
        """True iff the op_list consists of native operations only."""
        if ad.Adonis.is_native_operation(op_or_op_list):
            return True
        for op in op_or_op_list:
            if not ad.Adonis.is_native_operation(op):
                raise TypeError('Non-native operation: {}'.format(op))
        return True

    @pytest.mark.parametrize('gate', native_1q_gates)
    def test_native_single_qubit_gates(self, adonis, gate):
        """Native single-qubit gates do not decompose further."""

        q0 = adonis.qubits[0]

        for op in (
                gate.on(q0),
                gate.on(q0).with_tags('tag_baz'),
        ):
            decomposition = adonis.decompose_operation_full(op)
            assert decomposition == [op]
            assert TestGateDecomposition.is_native(decomposition)

    @pytest.mark.parametrize('gate', non_native_1q_gates)
    def test_non_native_single_qubit_gates(self, adonis, gate):
        """Non-native single qubit gates should decompose into native gates."""

        q1 = adonis.qubits[1]

        for op in (
                gate.on(q1),
                gate.on(q1).with_tags('tag_baz'),
        ):
            decomposition = adonis.decompose_operation_full(op)
            assert TestGateDecomposition.is_native(decomposition)

    @pytest.mark.parametrize('gate', native_2q_gates)
    def test_native_two_qubit_gate(self, adonis, gate):
        """Native two-qubit gates do not decompose further."""

        q0, _, q2 = adonis.qubits[:3]

        for op in (
                gate.on(q0, q2),
                gate.on(q2, q0).with_tags('tag_baz'),
        ):
            decomposition = adonis.decompose_operation_full(op)
            assert decomposition == [op]
            assert TestGateDecomposition.is_native(decomposition)

    @pytest.mark.parametrize('gate', non_native_2q_gates)
    def test_non_native_two_qubit_gates(self, adonis, gate):
        """Non-native two-qubit gates should decompose into native gates."""

        q0, q1, q2 = adonis.qubits[:3]

        for op in (
                gate.on(q0, q2),
                gate.on(q2, q0).with_tags('tag_baz'),
                gate.on(q2, q1),
        ):
            decomposition = adonis.decompose_operation_full(op)
            assert TestGateDecomposition.is_native(decomposition)

            # matrix representations must match up to global phase
            U = cirq.Circuit(op)._unitary_()
            W = cirq.Circuit(decomposition)._unitary_()
            assert dist(U, W) == pytest.approx(0)


class TestCircuitValidation:
    """Validating entire circuits."""

    def test_valid_circuit(self, adonis):
        """A valid circuit should pass validation."""
        q0, q1 = adonis.qubits[:2]

        valid_circuit = cirq.Circuit(device=adonis)
        valid_circuit.append(cirq.Y(q0))
        valid_circuit.append(cirq.measure(q0, key='a'))
        valid_circuit.append(cirq.measure(q1, key='b'))

        adonis.validate_circuit(valid_circuit)

    def test_invalid_circuit(self, adonis):
        """An invalid circuit should not pass validation."""

        q0, q1 = adonis.qubits[:2]

        invalid_circuit = cirq.Circuit(device=adonis)
        invalid_circuit.append(cirq.Y(q0))
        invalid_circuit.append(cirq.measure(q0, key='a'))
        invalid_circuit.append(cirq.measure(q1, key='a'))

        with pytest.raises(ValueError, match='Measurement key a repeated'):
            adonis.validate_circuit(invalid_circuit)
