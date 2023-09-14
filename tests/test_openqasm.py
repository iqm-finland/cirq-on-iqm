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
"""Testing OpenQASM 2.0 import/export.
"""
import cirq
import numpy as np
import pytest

from iqm.cirq_iqm.extended_qasm_parser import QasmUGate, circuit_from_qasm


@pytest.mark.parametrize(
    'qasm, op',
    [
        ('U(pi * 0.1, pi * 0.2, pi * 0.3) q[0];', QasmUGate(theta=0.1, phi=0.2, lmda=0.3)),
        ('u3(pi * 0.1, pi * 0.2, pi * 0.3) q[0];', QasmUGate(theta=0.1, phi=0.2, lmda=0.3)),
        ('CX q[0], q[1];', cirq.CNOT),
        (
            'U(pi * 0.4, pi * 0.25, pi * -0.25) q[0];',
            cirq.PhasedXPowGate(phase_exponent=0.75, global_shift=-0.5) ** 0.4,
        ),
        (
            'u3(pi * 0.4, pi * 0.25, pi * -0.25) q[0];',
            cirq.PhasedXPowGate(phase_exponent=0.75, global_shift=-0.5) ** 0.4,
        ),
        ('cz q[0], q[1];', cirq.CZ),
        ('measure q[0] -> c[0];', cirq.MeasurementGate(1, 'c_0')),
    ],
)
def test_qasm_to_circuit(qasm, op):
    """Check that the extended QASM parser correctly imports various operations."""
    preamble = """
OPENQASM 2.0;
include "qelib1.inc";

qreg q[2];
creg c[1];
"""
    c = circuit_from_qasm(preamble + qasm)
    assert len(c) == 1
    assert c[0].operations[0].gate == op


@pytest.mark.parametrize(
    'op, qasm',
    [
        (QasmUGate(theta=0.1, phi=0.2, lmda=0.3), 'u3(pi*0.1,pi*0.2,pi*0.3) q[0];'),
        (cirq.CNOT, 'cx q[0],q[1];'),
        # NOTE the addition of pi to the phase angle, and negation of the rotation angle (Cirq convention)
        (cirq.PhasedXPowGate(phase_exponent=0.75, global_shift=-0.5) ** 0.4, 'u3(pi*-0.4, pi*1.25, pi*-1.25) q[0];'),
        (cirq.CZ, 'cz q[0],q[1];'),
        (cirq.MeasurementGate(1, 'key'), 'measure q[0] -> m_key[0];'),
    ],
)
def test_circuit_to_qasm(op, qasm):
    """Check that Cirq exports various operations as OpenQASM in the expected way."""

    qubits = [cirq.NamedQubit('Alice'), cirq.NamedQubit('Bob')]
    c = cirq.Circuit()
    c.append(op(*qubits[: op._num_qubits_()]))

    got_qasm = c.to_qasm()
    assert got_qasm.endswith(qasm + '\n')


def test_round_trip():
    """Circuit into OpenQASM and back."""

    # This is how Cirq always names the exported qubits
    qubits = [cirq.NamedQubit('q_0'), cirq.NamedQubit('q_1')]
    old = cirq.Circuit(
        cirq.X(qubits[0]),
        cirq.Y(qubits[0]),
        cirq.Z(qubits[0]),
        # XPowGate etc are imported as rx
        cirq.rx(np.pi * 0.1)(qubits[0]),
        cirq.ry(np.pi * 0.2)(qubits[0]),
        cirq.rz(np.pi * 0.3)(qubits[0]),
        cirq.CZ(*qubits),
        cirq.CNOT(*qubits),
        cirq.SWAP(*qubits),
        # cirq.PhasedXPowGate(exponent=0.2, phase_exponent=0.1, global_shift=-0.5)(qubits[0]),
        # PhasedXPowGate won't make it back in the exact same form,
        # because neither U(a, b, c) nor PhasedXPowGate(e, p) is an injective map, and Cirq exports
        # PhasedXPowGate as a different preimage of U than the one our import function uses.
    )
    qasm = old.to_qasm()
    new = circuit_from_qasm(qasm)

    # they correspond to the same propagator
    assert cirq.unitary(old) == pytest.approx(cirq.unitary(new))
    # gate-by-gate they are the same circuit
    assert new == old
