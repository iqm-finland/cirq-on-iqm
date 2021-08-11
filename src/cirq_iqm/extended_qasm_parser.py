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
Extends the OpenQASM 2.0 language by gates native to the IQM architectures.
"""
import cirq
from cirq.contrib.qasm_import._parser import QasmGateStatement, QasmParser

from cirq_iqm.iqm_gates import IsingGate, XYGate


def circuit_from_qasm(qasm: str) -> cirq.circuits.Circuit:
    """Parses an OpenQASM 2.0 program to a Cirq circuit.

    The OpenQASM language has been extended by the ``iswap``, ``sqrt_iswap``,
    :func:`ising <.iqm_gates.IsingGate>` and :func:`xy <.iqm_gates.XYGate>` gates.

    Args:
        qasm: OpenQASM string

    Returns:
        parsed circuit
    """
    parser = QasmParser()
    parser.all_gates['ising'] = QasmGateStatement(
        qasm_gate='ising',
        cirq_gate=lambda params: IsingGate(params[0]),
        num_params=1,
        num_args=2
    )
    parser.all_gates['xy'] = QasmGateStatement(
        qasm_gate='xy',
        cirq_gate=lambda params: XYGate(params[0]),
        num_params=1,
        num_args=2
    )
    parser.all_gates['iswap'] = QasmGateStatement(
        qasm_gate='iswap',
        cirq_gate=cirq.ops.ISWAP,
        num_params=0,
        num_args=2
    )
    parser.all_gates['sqrt_iswap'] = QasmGateStatement(
        qasm_gate='sqrt_iswap',
        cirq_gate=cirq.ops.ISwapPowGate(exponent=0.5),
        num_params=0,
        num_args=2
    )
    return parser.parse(qasm).circuit
