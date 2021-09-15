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
import pytest

from cirq_iqm.extended_qasm_parser import QasmUGate, circuit_from_qasm


@pytest.mark.parametrize('qasm, op', [
    ('U(pi * 0.1, pi * 0.2, pi * 0.3) q[0];', QasmUGate(theta=0.1, phi=0.2, lmda=0.3)),
    ('CX q[0], q[1];', cirq.CNOT),
    ('U(pi * 0.4, pi * 0.25, pi * -0.25) q[0];', cirq.PhasedXPowGate(phase_exponent=0.75, global_shift=-0.5) ** 0.4),
    ('cz q[0], q[1];', cirq.CZ),
    ('measure q[0] -> c[0];', cirq.MeasurementGate(1, 'c_0')),
])
def test_qasm_to_circuit(qasm, op):
    """Check that the extended QASM parser imports correctly various operations."""
    preamble = """
OPENQASM 2.0;
include "qelib1.inc";

qreg q[2];
creg c[1];
"""
    c = circuit_from_qasm(preamble + qasm)
    assert len(c) == 1
    assert c[0].operations[0].gate == op


@pytest.mark.parametrize('qasm, op', [
    ('u3(pi*0.1,pi*0.2,pi*0.3) q[0];', QasmUGate(theta=0.1, phi=0.2, lmda=0.3)),
    ('cx q[0],q[1];', cirq.CNOT),
    # NOTE the addition of pi to the phase angle, and negation of the rotation angle (Cirq convention)
    ('u3(pi*-0.4, pi*1.25, pi*-1.25) q[0];', cirq.PhasedXPowGate(phase_exponent=0.75, global_shift=-0.5) ** 0.4),
    ('cz q[0],q[1];', cirq.CZ),
    ('measure q[0] -> m_key[0];', cirq.MeasurementGate(1, 'key')),
])
def test_circuit_to_qasm(qasm, op):
    """Check that the extended QASM parser exports correctly various operations."""

    qubits = [cirq.NamedQubit('Alice'), cirq.NamedQubit('Bob')]
    c = cirq.Circuit()
    c.append(op(*qubits[:op._num_qubits_()]))

    got_qasm = c.to_qasm()
    assert got_qasm.endswith(qasm + '\n')
