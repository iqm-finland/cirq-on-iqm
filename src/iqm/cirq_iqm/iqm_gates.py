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
Implementations for IQM specific quantum gates
"""
from typing import List, Tuple

from cirq import CircuitDiagramInfo, CircuitDiagramInfoArgs, EigenGate
import numpy as np


class IQMMoveGate(EigenGate):
    r"""The MOVE operation is a unitary population exchange operation between a qubit and a resonator.
    Its effect is only defined in the invariant subspace :math:`S = \text{span}\{|00\rangle, |01\rangle, |10\rangle\}`,
    where it swaps the populations of the states :math:`|01\rangle` and :math:`|10\rangle`.
    Its effect on the orthogonal subspace is undefined.

    MOVE has the following presentation in the subspace :math:`S`:

    .. math:: \text{MOVE}_S = |00\rangle \langle 00| + a |10\rangle \langle 01| + a^{-1} |01\rangle \langle 10|,

    where :math:`a` is an undefined complex phase that is canceled when the MOVE gate is applied a second time.

    To ensure that the state of the qubit and resonator has no overlap with :math:`|11\rangle`, it is
    recommended that no single qubit gates are applied to the qubit in between a
    pair of MOVE operations.

    Note: At this point the locus for the move gate must be defined in the order: ``[qubit, resonator]``.
    Additionally, the matrix representation of the gate set to be a SWAP gate, even though this is not what physically
    happens.
    """

    def _num_qubits_(self) -> int:
        return 2

    def _eigen_components(self) -> List[Tuple[float, np.ndarray]]:
        return [
            (0, np.array([[1, 0, 0, 0], [0, 0.5, 0.5, 0], [0, 0.5, 0.5, 0], [0, 0, 0, 1]])),
            (1, np.array([[0, 0, 0, 0], [0, 0.5, -0.5, 0], [0, -0.5, 0.5, 0], [0, 0, 0, 0]])),
        ]

    def _circuit_diagram_info_(self, args: CircuitDiagramInfoArgs) -> CircuitDiagramInfo:
        return CircuitDiagramInfo(wire_symbols=('MOVE(QB)', 'MOVE(Res)'), exponent=self._diagram_exponent(args))

    def __str__(self) -> str:
        return 'MOVE'
