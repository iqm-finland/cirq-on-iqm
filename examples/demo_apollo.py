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
Demonstrates importing a quantum circuit from an OpenQASM 2.0 file, transforming it into
the Apollo native gateset and connectivity, and then executing it on a simulator.
"""
import cirq
from demo_common import demo

from cirq_iqm.devices import Apollo
from cirq_iqm.extended_qasm_parser import circuit_from_qasm


def demo_apollo(use_qsim: bool = False) -> None:
    """Run the demo using the Apollo architecture."""

    print('\nApollo demo\n===========\n')
    device = Apollo()
    qasm_program = """
        OPENQASM 2.0;
        include "qelib1.inc";

        qreg q[6];
        creg meas[6];

        U(0.2, 0.5, 1.7) q[1];
        h q[0];
        h q[2];
        h q[3];
        h q[4];
        h q[5];
        cx q[1], q[2];
        cx q[2], q[5];
        cx q[3], q[4];
        cx q[0], q[1];
        measure q -> meas;
    """
    circuit = circuit_from_qasm(qasm_program)

    # add some more gates
    q2 = cirq.NamedQubit('q_2')
    q3 = cirq.NamedQubit('q_3')
    circuit.insert(len(circuit) - 2, cirq.CXPowGate(exponent=0.723)(q2, q3))

    demo(device, circuit, use_qsim=use_qsim)


if __name__ == '__main__':
    demo_apollo()
