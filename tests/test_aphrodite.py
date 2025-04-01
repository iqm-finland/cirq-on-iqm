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

"""Tests for the Aphrodite device.
"""
# pylint: disable=redefined-outer-name,no-self-use,duplicate-code

from __future__ import annotations

import cirq
import numpy as np
import pytest

from iqm.cirq_iqm import Aphrodite


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
def aphrodite():
    """Aphrodite device fixture."""
    return Aphrodite()


# define various groups of gates to test

native_1q_gates = [
    cirq.X,
    cirq.Y,
    cirq.XPowGate(exponent=0.23),
    cirq.YPowGate(exponent=0.71),
    cirq.PhasedXPowGate(phase_exponent=1.7, exponent=-0.58),
]

native_2q_gates = [
    cirq.CZ,
]

non_native_1q_gates = [
    cirq.H,
    cirq.Z,
    cirq.ZPowGate(exponent=-0.23),
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
    def test_native_single_qubit_gates(self, aphrodite, gate, q):
        """Native operations must pass validation."""

        aphrodite.validate_operation(gate(aphrodite.qubits[q]))
        aphrodite.validate_operation(gate(aphrodite.qubits[q]).with_tags('tag_foo'))

    @pytest.mark.parametrize('gate', native_2q_gates)
    def test_native_two_qubit_gates(self, aphrodite, gate):
        """Native operations must pass validation."""

        q0, q1 = aphrodite.qubits[:2]

        aphrodite.validate_operation(gate(q0, q1))
        aphrodite.validate_operation(gate(q1, q0))

    @pytest.mark.parametrize(
        'meas',
        [
            cirq.measure,
            lambda q: cirq.measure(q, key='test'),
        ],
    )
    def test_native_measurements(self, aphrodite, meas):
        """Native operations must pass validation."""

        aphrodite.validate_operation(meas(aphrodite.qubits[0]))

    @pytest.mark.parametrize('gate', non_native_1q_gates)
    def test_non_native_single_qubit_gates(self, aphrodite, gate):
        """Non-native operations must not pass validation."""

        q0 = aphrodite.qubits[0]

        with pytest.raises(ValueError, match='Unsupported gate type'):
            aphrodite.validate_operation(gate(q0))

        with pytest.raises(ValueError, match='Unsupported gate type'):
            aphrodite.validate_operation(gate(q0).with_tags('tag_foo'))

    @pytest.mark.parametrize('gate', non_native_2q_gates)
    def test_non_native_two_qubit_gates(self, aphrodite, gate):
        """Non-native operations must not pass validation."""

        q0, q1 = aphrodite.qubits[:2]

        with pytest.raises(ValueError, match='Unsupported gate type'):
            aphrodite.validate_operation(gate(q0, q1))

        with pytest.raises(ValueError, match='Unsupported gate type'):
            aphrodite.validate_operation(gate(q1, q0))

    @pytest.mark.parametrize(
        'qubit',
        [
            cirq.NamedQubit('xxx'),
            cirq.GridQubit(0, 1),
        ],
    )
    def test_qubits_not_on_device(self, aphrodite, qubit):
        """Gates operating on qubits not on device must not pass validation."""

        with pytest.raises(ValueError, match='Qubit not on device'):
            aphrodite.validate_operation(cirq.X(qubit))

    @pytest.mark.parametrize('gate', native_2q_gates)
    def test_qubits_not_connected(self, aphrodite, gate):
        """Native two-qubit gates operating on non-connected qubits must not pass validation."""

        q0, _, q2 = aphrodite.qubits[:3]

        with pytest.raises(ValueError, match='Unsupported operation between qubits'):
            aphrodite.validate_operation(gate(q0, q2))

        with pytest.raises(ValueError, match='Unsupported operation between qubits'):
            aphrodite.validate_operation(gate(q2, q0))


class TestGateDecomposition:
    """Decomposing gates."""

    @staticmethod
    def is_native(aphrodite, op_or_op_list) -> bool:
        """True iff the op_list consists of native operations of aphrodite only."""
        if aphrodite.is_native_operation(op_or_op_list):
            return True
        for op in op_or_op_list:
            if not aphrodite.is_native_operation(op):
                raise TypeError(f'Non-native operation: {op}')
        return True

    @pytest.mark.parametrize('gate', native_1q_gates)
    def test_native_single_qubit_gates(self, aphrodite, gate):
        """Native single-qubit gates do not decompose further."""

        q0 = aphrodite.qubits[0]

        for op in (
            gate.on(q0),
            gate.on(q0).with_tags('tag_baz'),
        ):
            decomposition = aphrodite.decompose_operation(op)
            assert decomposition == op
            assert TestGateDecomposition.is_native(aphrodite, decomposition)

    @pytest.mark.parametrize('gate', non_native_1q_gates)
    def test_non_native_single_qubit_gates(self, aphrodite, gate):
        """Non-native single qubit gates should decompose into native gates."""

        q1 = aphrodite.qubits[1]

        for op in (
            gate.on(q1),
            gate.on(q1).with_tags('tag_baz'),
        ):
            decomposition = aphrodite.decompose_operation(op)
            assert TestGateDecomposition.is_native(aphrodite, decomposition)

    @pytest.mark.parametrize('gate', native_2q_gates)
    def test_native_two_qubit_gate(self, aphrodite, gate):
        """Native two-qubit gates do not decompose further."""

        q0, _, q2 = aphrodite.qubits[:3]

        for op in (
            gate.on(q0, q2),
            gate.on(q2, q0).with_tags('tag_baz'),
        ):
            decomposition = aphrodite.decompose_operation(op)
            assert decomposition == op
            assert TestGateDecomposition.is_native(aphrodite, decomposition)

    @pytest.mark.parametrize('gate', non_native_2q_gates)
    def test_non_native_two_qubit_gates(self, aphrodite, gate):
        """Non-native two-qubit gates should decompose into native gates."""

        q0, q1, q2 = aphrodite.qubits[:3]

        for op in (
            gate.on(q0, q2),
            gate.on(q2, q0).with_tags('tag_baz'),
            gate.on(q2, q1),
        ):
            decomposition = aphrodite.decompose_operation(op)
            assert TestGateDecomposition.is_native(aphrodite, decomposition)

            # matrix representations must match up to global phase
            U = cirq.Circuit(op)._unitary_()
            W = cirq.Circuit(decomposition)._unitary_()
            assert dist(U, W) == pytest.approx(0)


class TestCircuitValidation:
    """Validating entire circuits."""

    def test_valid_circuit(self, aphrodite):
        """A valid circuit should pass validation."""
        q0, q1 = aphrodite.qubits[:2]

        valid_circuit = cirq.Circuit()
        valid_circuit.append(cirq.Y(q0))
        valid_circuit.append(cirq.measure(q0, key='a'))
        valid_circuit.append(cirq.measure(q1, key='b'))

        aphrodite.validate_circuit(valid_circuit)

    def test_invalid_circuit(self, aphrodite):
        """An invalid circuit should not pass validation."""

        q0, q1 = aphrodite.qubits[:2]

        invalid_circuit = cirq.Circuit()
        invalid_circuit.append(cirq.Y(q0))
        invalid_circuit.append(cirq.measure(q0, key='a'))
        invalid_circuit.append(cirq.measure(q1, key='a'))

        with pytest.raises(ValueError, match='Measurement key a repeated'):
            aphrodite.validate_circuit(invalid_circuit)


class TestCircuitDecomposition:
    def test_decompose_circuit_native_only(self, aphrodite):
        """Circuit containing only native ops decomposes trivially."""
        q0, q1 = cirq.NamedQubit.range(0, 2, prefix='qubit_')
        circuit = cirq.Circuit(
            cirq.CZ(q0, q1),
        )
        new = aphrodite.decompose_circuit(circuit)

        assert new == circuit

    def test_decompose_circuit(self, aphrodite):
        """Any gates should be decomposable to native gates."""
        q0, q1 = cirq.NamedQubit.range(0, 2, prefix='qubit_')
        circuit = cirq.Circuit(
            cirq.CNOT(q0, q1),
        )
        new = aphrodite.decompose_circuit(circuit)

        # still uses the original qubits, not device qubits
        assert circuit.all_qubits() == new.all_qubits()
        assert len(new) == 3
        assert new[1].operations[0].gate == cirq.CZ  # CNOT decomposes into CZ plus Ry:s

    def test_decompose_complicated_circuit(self, aphrodite):
        """Can handle even 3-qubit gates."""
        q0, q1, q2 = cirq.NamedQubit.range(0, 3, prefix='qubit_')
        circuit = cirq.Circuit(cirq.H(q0), cirq.X(q1), cirq.TOFFOLI(q0, q2, q1), cirq.measure(q0, q1, q2, key='mk'))
        new = aphrodite.decompose_circuit(circuit)

        # still uses the original qubits, not device qubits
        assert circuit.all_qubits() == new.all_qubits()
        assert len(new) == 31


def check_measurement(op, key: str) -> None:
    """Check that the given operation is a measurement with the expected key."""
    assert isinstance(op.gate, cirq.MeasurementGate)
    assert op.gate.key == key
    assert len(op.qubits) == 1


class TestCircuitRouting:
    @pytest.fixture(scope='class')
    def qubits(self):
        return [
            cirq.NamedQubit('Alice'),
            cirq.NamedQubit('Bob'),
            cirq.NamedQubit('Charlie'),
            cirq.NamedQubit('Dan'),
            cirq.NamedQubit('Eve'),
            cirq.NamedQubit('Faythe'),
            cirq.NamedQubit('Grace'),
            cirq.NamedQubit('Heidi'),
            cirq.NamedQubit('Ivan'),
            cirq.NamedQubit('Judy'),
            cirq.NamedQubit('Kiuas'),
            cirq.NamedQubit('Leon'),
            cirq.NamedQubit('Mallory'),
            cirq.NamedQubit('Niaj'),
            cirq.NamedQubit('Olivia'),
            cirq.NamedQubit('Peggy'),
            cirq.NamedQubit('Quant'),
            cirq.NamedQubit('Rupert'),
            cirq.NamedQubit('Sybil'),
            cirq.NamedQubit('Trent'),
            cirq.NamedQubit('Alice2'),
            cirq.NamedQubit('Bob2'),
            cirq.NamedQubit('Charlie2'),
            cirq.NamedQubit('Dan2'),
            cirq.NamedQubit('Eve2'),
            cirq.NamedQubit('Faythe2'),
            cirq.NamedQubit('Grace2'),
            cirq.NamedQubit('Heidi2'),
            cirq.NamedQubit('Ivan2'),
            cirq.NamedQubit('Judy2'),
            cirq.NamedQubit('Kiuas2'),
            cirq.NamedQubit('Leon2'),
            cirq.NamedQubit('Mallory2'),
            cirq.NamedQubit('Niaj2'),
            cirq.NamedQubit('Olivia2'),
            cirq.NamedQubit('Peggy2'),
            cirq.NamedQubit('Quant2'),
            cirq.NamedQubit('Rupert2'),
            cirq.NamedQubit('Sybil2'),
            cirq.NamedQubit('Trent2'),
            cirq.NamedQubit('Alice3'),
            cirq.NamedQubit('Bob3'),
            cirq.NamedQubit('Charlie3'),
            cirq.NamedQubit('Dan3'),
            cirq.NamedQubit('Eve3'),
            cirq.NamedQubit('Faythe3'),
            cirq.NamedQubit('Grace3'),
            cirq.NamedQubit('Heidi3'),
            cirq.NamedQubit('Ivan3'),
            cirq.NamedQubit('Judy3'),
            cirq.NamedQubit('Kiuas3'),
            cirq.NamedQubit('Leon3'),
            cirq.NamedQubit('Mallory3'),
            cirq.NamedQubit('Niaj3'),
        ]

    def test_routing_with_partial_initial_mapping(self, aphrodite, qubits):
        circuit = cirq.Circuit(
            cirq.CZ(qubits[0], qubits[1]),
            cirq.measure(qubits[0], key='mk0'),
            cirq.measure(qubits[1], key='mk1'),
        )

        initial_mapper = cirq.HardCodedInitialMapper(dict(zip(qubits[0:2], aphrodite.metadata.nx_graph)))
        # route_circuit() checks mapping consistency when initial_mapper is provided
        new, _, _ = aphrodite.route_circuit(circuit, initial_mapper=initial_mapper)

        aphrodite.validate_circuit(new)

    def test_routing_with_complete_initial_mapping(self, aphrodite, qubits):
        circuit = cirq.Circuit(
            [
                cirq.CZ(qubits[0], qubits[1]),
                cirq.CZ(qubits[0], qubits[2]),
                cirq.CZ(qubits[2], qubits[4]),
            ]
            + [cirq.measure([q]) for q in qubits]
        )

        initial_mapper = cirq.HardCodedInitialMapper(dict(zip(qubits, aphrodite.metadata.nx_graph)))
        # route_circuit() checks mapping consistency when initial_mapper is provided
        new, _, _ = aphrodite.route_circuit(circuit, initial_mapper=initial_mapper)
        new = aphrodite.decompose_circuit(new)

        aphrodite.validate_circuit(new)

    def test_routing_circuit_too_large(self, aphrodite):
        """The circuit must fit on the device."""
        qubits = cirq.NamedQubit.range(0, 55, prefix='qubit_')
        circuit = cirq.Circuit([cirq.X(q) for q in qubits])
        with pytest.raises(ValueError, match='No available physical qubits left on the device.'):
            aphrodite.route_circuit(circuit)

    def test_routing_without_SWAPs(self, aphrodite, qubits):
        """Circuit graph can be embedded in the aphrodite connectivity graph, no SWAPs needed."""
        circuit = cirq.Circuit(cirq.CZ(*qubits[0:2]), cirq.CZ(*qubits[2:4]))
        new, _, _ = aphrodite.route_circuit(circuit)

        assert len(new.all_qubits()) == 4
        assert new.all_qubits() <= set(aphrodite.qubits)
        # assert len(new) == len(circuit)  # TODO at the moment the routing algo may add unnecessary SWAPs

    def test_routing_needs_SWAPs(self, aphrodite, qubits):
        """Circuit has direct cyclic connectivity with 3 qubits, aphrodite doesn't, so SWAPs are needed."""
        circuit = cirq.Circuit(
            cirq.CZ(qubits[0], qubits[1]), cirq.CZ(qubits[0], qubits[2]), cirq.CZ(qubits[1], qubits[2])
        )
        new, _, _ = aphrodite.route_circuit(circuit)

        assert len(new.all_qubits()) >= 3  # routing algo may use more qubits
        assert new.all_qubits() <= set(aphrodite.qubits)
        assert len(new) == 4  # a SWAP gate was added

        # SWAPs added by routing can be decomposed
        with pytest.raises(ValueError, match='Unsupported gate type: cirq.SWAP'):
            aphrodite.validate_circuit(new)
        decomposed = aphrodite.decompose_circuit(new)
        aphrodite.validate_circuit(decomposed)

    def test_valid_routed_circuit(self, aphrodite, qubits):
        """A valid routed circuit should pass validation."""

        circuit = cirq.Circuit(
            cirq.CZ(qubits[0], qubits[1]),
            cirq.CZ(qubits[0], qubits[2]),
            cirq.CZ(qubits[0], qubits[3]),
            cirq.CZ(qubits[0], qubits[4]),
            cirq.CZ(qubits[0], qubits[5]),
        )
        print('routing started')
        print(circuit)
        routed_circuit, _, _ = aphrodite.route_circuit(circuit)
        print('decomposing')
        print(routed_circuit)
        valid_circuit = aphrodite.decompose_circuit(routed_circuit)
        print('validating')
        print(valid_circuit)
        aphrodite.validate_circuit(valid_circuit)
        print('done')

    @pytest.mark.parametrize(
        'qid',
        [
            cirq.LineQubit(4),
            cirq.GridQubit(5, 6),
            cirq.NamedQid('Quentin', dimension=2),
            cirq.LineQid(4, dimension=2),
            cirq.GridQid(5, 6, dimension=2),
        ],
    )
    def test_routing_with_qids(self, aphrodite, qid):
        """Routing can handle all kinds of Qid types, not just NamedQubit."""
        q = cirq.NamedQubit('Alice')
        circuit = cirq.Circuit(
            cirq.X(q),
            cirq.Y(qid),
            cirq.CZ(q, qid),
        )
        new, _, _ = aphrodite.route_circuit(circuit)

        assert len(new.all_qubits()) == 2
        assert new.all_qubits() <= set(aphrodite.qubits)

    def test_routed_measurements(self, aphrodite, qubits):
        circuit = cirq.Circuit(
            cirq.CZ(qubits[0], qubits[2]),
            cirq.CZ(*qubits[0:2]),
            cirq.CZ(*qubits[1:3]),
            cirq.measure(qubits[0:3], key='mk'),
        )

        circuit, initial_mapping, final_mapping = aphrodite.route_circuit(circuit)

        assert circuit.are_all_measurements_terminal()
        assert circuit.all_measurement_key_names() == {'mk'}

        # Check that measurements in the routed circuit are mapped to correct qubits
        measurements = [op for _, op, _ in circuit.findall_operations_with_gate_type(cirq.MeasurementGate)]
        assert all(len(op.qubits) == 3 for op in measurements)

        mk_to_physical = {op.gate.key: [cirq.NamedQubit(q.name) for q in op.qubits] for op in measurements}
        routed_physical_to_logical_mapping = {final_mapping[v]: k for k, v in initial_mapping.items()}
        measured_logical_qubits = [routed_physical_to_logical_mapping[q] for q in mk_to_physical['mk']]
        assert measured_logical_qubits == qubits[0:3]

    def test_routing_with_multi_qubit_measurements(self, aphrodite, qubits):
        circuit = cirq.Circuit(
            *(cirq.CZ(qubits[i], qubits[i + 1]) for i in range(53)),
            cirq.measure(*qubits[0:2], key='m1'),
            cirq.measure(*qubits[2:54], key='m2'),
        )
        new, _, _ = aphrodite.route_circuit(circuit)
        assert new.all_qubits() == set(aphrodite.qubits)
        # Test that all measurements exist.
        assert new.all_measurement_key_names() == {'m1', 'm2'}

    def test_routing_with_mid_circuit_measurements(self, aphrodite, qubits):
        circuit = cirq.Circuit(
            cirq.X(qubits[0]),
            cirq.measure(qubits[0], key='mid'),
            cirq.Y(qubits[0]),
            cirq.measure(qubits[0], key='final'),
        )

        new, _, _ = aphrodite.route_circuit(circuit)

        # just one qubit used
        assert len(new.all_qubits()) == 1
        # Test that all measurements exist.
        assert new.all_measurement_key_names() == {'mid', 'final'}

        check_measurement(new[1].operations[0], key='mid')
        check_measurement(new[3].operations[0], key='final')
