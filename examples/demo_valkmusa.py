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
Demonstrates importing a quantum circuit from an OpenQASM 2.0 file, transforming it into
the Valkmusa native gateset and connectivity, and then executing it on a simulator.
"""
import cirq
from demo_common import demo

from cirq_iqm.extended_qasm_parser import circuit_from_qasm
from cirq_iqm.valkmusa import Valkmusa


def demo_valkmusa(do_measure=False, use_qsim=False):
    """Run the demo using the Valkmusa architecture."""

    print('\nValkmusa demo\n=============\n')
    device = Valkmusa()
    qasm_program = """
        OPENQASM 2.0;
        include "qelib1.inc";
        qreg q[2];
        creg meas[2];
        U(1.3, 0.4, -0.3) q[1];
        h q[0];
        rx(1.1) q[0];
        cx q[0], q[1];
        xy(0.7) q[1], q[0];  // QASM extension
    """
    if do_measure:
        qasm_program += '\nmeasure q -> meas;'

    circuit = circuit_from_qasm(qasm_program)

    # add some more gates
    q0 = cirq.NamedQubit('q_0')
    q1 = cirq.NamedQubit('q_1')
    circuit.insert(len(circuit) - 1, cirq.ISwapPowGate(exponent=0.4)(q0, q1))

    qubit_mapping = {'q_0': 'QB1', 'q_1': 'QB2'}
    demo(device, circuit, do_measure, use_qsim=use_qsim, qubit_mapping=qubit_mapping)


if __name__ == '__main__':
    demo_valkmusa()
