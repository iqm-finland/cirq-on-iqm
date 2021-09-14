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
from cirq.contrib.qasm_import._parser import QasmParser


def circuit_from_qasm(qasm: str) -> cirq.circuits.Circuit:
    """Parses an OpenQASM 2.0 program to a Cirq circuit.

   TODO The previous functionality that contained additional 2-qubit gates has now been removed as obsolete.
        This function remains because new parsing logic will be introduced in a future PR.

    Args:
        qasm: OpenQASM string

    Returns:
        parsed circuit
    """
    parser = QasmParser()
    return parser.parse(qasm).circuit
