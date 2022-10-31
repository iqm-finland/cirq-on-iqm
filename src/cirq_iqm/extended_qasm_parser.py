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
Imports OpenQASM 2.0 programs in a way that preserves gates native to the IQM architectures.
"""
import cirq
from cirq.contrib.qasm_import._parser import QasmGateStatement, QasmParser, QasmUGate
import numpy as np


def circuit_from_qasm(qasm: str) -> cirq.circuits.Circuit:
    """Parses an OpenQASM 2.0 program to a Cirq circuit.

    Args:
        qasm: OpenQASM program

    Returns:
        parsed circuit
    """
    parser = QasmParser()

    def convert_U(args: list[float]) -> cirq.Gate:
        """Maps the OpenQASM builtin one-qubit gate ``U`` to :class:`cirq.QasmUGate`,
        or :class:`cirq.PhasedXPowGate` if possible.
        """
        theta, phi, lmda = args
        scale = np.pi
        if phi == -lmda:
            return cirq.PhasedXPowGate(exponent=theta / scale, phase_exponent=phi / scale + 0.5, global_shift=-0.5)
        return QasmUGate(*(p / np.pi for p in args))

    rule = QasmGateStatement(
        qasm_gate='U',
        num_params=3,
        num_args=1,
        cirq_gate=convert_U,
    )
    parser.basic_gates['U'] = rule
    parser.all_gates['U'] = rule
    # u3 is not a basic OpenQASM gate
    parser.all_gates['u3'] = QasmGateStatement(
        qasm_gate='u3',
        num_params=3,
        num_args=1,
        cirq_gate=convert_U,
    )
    return parser.parse(qasm).circuit
