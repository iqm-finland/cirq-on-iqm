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

"""Tests for the Valkmusa device.
"""
import cirq

# pylint: disable=redefined-outer-name,no-self-use,duplicate-code
import pytest

from cirq_iqm import Valkmusa


@pytest.fixture(scope='module')
def valkmusa():
    """Valkmusa device fixture."""
    return Valkmusa()


# define various groups of gates to test

native_1q_gates = [
    cirq.X,
    cirq.Y,
    cirq.XPowGate(exponent=0.23),
    cirq.YPowGate(exponent=0.71),
    cirq.PhasedXPowGate(phase_exponent=1.7, exponent=-0.58),
]

native_2q_gates = [
    cirq.ISWAP,
    cirq.ISwapPowGate(exponent=0.27),
]

non_native_1q_gates = [
    cirq.H,
    cirq.Z,
    cirq.ZPowGate(exponent=-0.23),
    cirq.HPowGate(exponent=-0.55),
    cirq.PhasedXZGate(x_exponent=0.2, z_exponent=-0.5, axis_phase_exponent=0.75),
]

non_native_2q_gates = [
    cirq.SWAP,
    cirq.CNOT,
    cirq.CXPowGate(exponent=-2.2),
    cirq.CZ,
    cirq.CZPowGate(exponent=1.6),
    cirq.ZZPowGate(exponent=1.3),
]


class TestOperationValidation:
    """Nativity and validation of various operations."""

    @pytest.mark.parametrize('gate', native_1q_gates)
    def test_native_single_qubit_gates(self, valkmusa, gate):
        """Native operations must pass validation."""

        QB1, QB2 = valkmusa.qubits
        valkmusa.validate_operation(gate(QB2))
        valkmusa.validate_operation(gate(QB1).with_tags('tag_foo'))

    @pytest.mark.parametrize('gate', native_2q_gates)
    def test_native_two_qubit_gates(self, valkmusa, gate):
        """Native operations must pass validation."""

        QB1, QB2 = valkmusa.qubits
        valkmusa.validate_operation(gate(QB1, QB2))
        valkmusa.validate_operation(gate(QB2, QB1))

    @pytest.mark.parametrize(
        'meas',
        [
            cirq.measure,
            lambda q: cirq.measure(q, key='test'),
        ],
    )
    def test_native_measurements(self, valkmusa, meas):
        """Native operations must pass validation."""

        QB1 = valkmusa.qubits[0]
        valkmusa.validate_operation(meas(QB1))

    @pytest.mark.parametrize('gate', non_native_1q_gates)
    def test_non_native_single_qubit_gates(self, valkmusa, gate):
        """Non-native operations must not pass validation."""

        QB1, QB2 = valkmusa.qubits

        with pytest.raises(ValueError, match='Unsupported gate type'):
            valkmusa.validate_operation(gate(QB2))

        with pytest.raises(ValueError, match='Unsupported gate type'):
            valkmusa.validate_operation(gate(QB1).with_tags('tag_foo'))

    @pytest.mark.parametrize('gate', non_native_2q_gates)
    def test_non_native_two_qubit_gates(self, valkmusa, gate):
        """Non-native operations must not pass validation."""

        QB1, QB2 = valkmusa.qubits
        with pytest.raises(ValueError, match='Unsupported gate type'):
            valkmusa.validate_operation(gate(QB1, QB2))

        with pytest.raises(ValueError, match='Unsupported gate type'):
            valkmusa.validate_operation(gate(QB2, QB1))

    @pytest.mark.parametrize(
        'qubit',
        [
            cirq.NamedQubit('xxx'),
        ],
    )
    def test_qubits_not_on_device(self, valkmusa, qubit):
        """Gates operating on qubits not on device must not pass validation."""

        with pytest.raises(ValueError, match='Qubit not on device'):
            valkmusa.validate_operation(cirq.X(qubit))


class TestGateDecomposition:
    """Decomposing gates."""

    @staticmethod
    def is_native(valkmusa, op_or_op_list) -> bool:
        """True iff the op_list consists of native operations of valkmusa only."""
        if valkmusa.is_native_operation(op_or_op_list):
            return True
        for op in op_or_op_list:
            if not valkmusa.is_native_operation(op):
                raise TypeError(f'Non-native operation: {op}')
        return True

    @pytest.mark.parametrize('gate', native_1q_gates)
    def test_native_single_qubit_gates(self, valkmusa, gate):
        """Native single-qubit gates do not decompose further."""

        QB1, QB2 = valkmusa.qubits

        for op in (
            gate.on(QB1),
            gate.on(QB2).with_tags('tag_baz'),
        ):
            decomposition = valkmusa.decompose_operation(op)
            assert decomposition == op
            assert TestGateDecomposition.is_native(valkmusa, decomposition)

    @pytest.mark.parametrize('gate', non_native_1q_gates)
    def test_non_native_single_qubit_gates(self, valkmusa, gate):
        """Non-native single qubit gates should decompose into native gates."""

        QB1, QB2 = valkmusa.qubits
        for op in (
            gate.on(QB1),
            gate.on(QB2).with_tags('tag_baz'),
        ):
            decomposition = valkmusa.decompose_operation(op)
            assert TestGateDecomposition.is_native(valkmusa, decomposition)

    @pytest.mark.parametrize('gate', native_2q_gates)
    def test_native_two_qubit_gates(self, valkmusa, gate):
        """Native two-qubit gates do not decompose further."""

        QB1, QB2 = valkmusa.qubits

        op = gate(QB1, QB2)
        decomposition = valkmusa.decompose_operation(op)
        assert decomposition == op
        assert TestGateDecomposition.is_native(valkmusa, decomposition)

    @pytest.mark.parametrize('gate', non_native_2q_gates)
    def test_non_native_two_qubit_gates(self, valkmusa, gate):
        """Non-native two-qubit gates should decompose into native gates."""

        QB1, QB2 = valkmusa.qubits

        for op in (
            gate(QB1, QB2),
            gate(QB2, QB1).with_tags('tag_baz'),
        ):
            decomposition = valkmusa.decompose_operation(op)
            assert TestGateDecomposition.is_native(valkmusa, decomposition)
