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
Native gates of the IQM quantum architectures in the Cirq framework.
"""
from typing import Optional, Tuple

import numpy as np
from cirq import ops, protocols
from cirq._compat import proper_repr


class IsingGate(ops.eigen_gate.EigenGate,
                ops.gate_features.TwoQubitGate,
                ops.gate_features.InterchangeableQubitsGate):
    r"""Rotates around the ZZ axis of the two-qubit Hilbert space.

    .. math::

       \text{Ising}(s) := \exp(-i Z \otimes Z \: \frac{\pi}{2} \: s), \quad \text{where} \: s \in [0, 2).

    Representing parameterized gate families in Cirq happens using the :class:`EigenGate` class,
    i.e. the exponent construction.

    We do not support most of the various Gate protocols.

    Cirq already has :class:`cirq.ops.ZZPowGate` which is equivalent to :class:`IsingGate` with a
    global phase, ``Ising(exponent=t, global_shift=s) = ZZPowGate(exponent=t, global_shift=s-0.5)``.
    """

    # the most important part, defines the gate family using a scaled spectral decomposition of the generator
    def _eigen_components(self):
        return [
            (-0.5, np.diag([1, 0, 0, 1])),
            (0.5, np.diag([0, 1, 1, 0])),
        ]

    # ZZ commutes with local Z rotations
    def _phase_by_(self, phase_turns, qubit_index):
        # pylint: disable=unused-argument
        return self

    def _circuit_diagram_info_(self, args: 'cirq.CircuitDiagramInfoArgs') -> 'cirq.CircuitDiagramInfo':
        return protocols.CircuitDiagramInfo(
            wire_symbols=('Ising', 'Ising'),
            exponent=self._diagram_exponent(args)
        )

    def _qasm_(self, args: 'cirq.QasmArgs',
               qubits: Tuple['cirq.Qid', ...]) -> Optional[str]:
        args.validate_version('2.0')
        return args.format('ising({}) {},{};\n', self._exponent, qubits[0], qubits[1])

    def __str__(self) -> str:
        return 'IsingGate({!r})'.format(self._exponent)

    def __repr__(self) -> str:
        if self._global_shift == 0:
            return 'cirq_iqm.IsingGate({})'.format(proper_repr(self._exponent))
        return (
            'cirq_iqm.IsingGate(exponent={}, '
            'global_shift={!r})'
        ).format(proper_repr(self._exponent), self._global_shift)


class XYGate(ops.eigen_gate.EigenGate,
             ops.gate_features.TwoQubitGate,
             ops.gate_features.InterchangeableQubitsGate):
    r"""Rotates around the XX+YY axis of the two-qubit Hilbert space.

    .. math::

       \text{XY}(s) := \exp(-i (X \otimes X +Y \otimes Y) \: \frac{\pi}{2} \: s), \quad \text{where} \: s \in [0, 2).

    We do not support most of the Gate protocols.

    :class:`XYGate` is a reparameterization of :class:`cirq.ops.ISwapPowGate` up to global phase,
    ``XYGate(exponent=t, global_shift=s) == ISwapPowGate(exponent=-2*t, global_shift=-s/2)``.
    """

    def _eigen_components(self):
        return [
            (0, np.diag([1, 0, 0, 1])),
            (-1, 0.5 * np.array([[0, 0, 0, 0],
                                 [0, 1, 1, 0],
                                 [0, 1, 1, 0],
                                 [0, 0, 0, 0]])),
            (1, 0.5 * np.array([[0, 0, 0, 0],
                                [0, 1, -1, 0],
                                [0, -1, 1, 0],
                                [0, 0, 0, 0]])),
        ]

    def _circuit_diagram_info_(self, args: 'cirq.CircuitDiagramInfoArgs') -> 'cirq.CircuitDiagramInfo':
        return protocols.CircuitDiagramInfo(
            wire_symbols=('XY', 'XY'),
            exponent=self._diagram_exponent(args)
        )

    def _qasm_(self, args: 'cirq.QasmArgs',
               qubits: Tuple['cirq.Qid', ...]) -> Optional[str]:
        args.validate_version('2.0')
        return args.format('xy({}) {},{};\n', self._exponent, qubits[0], qubits[1])

    def __str__(self) -> str:
        return 'XYGate({!r})'.format(self._exponent)

    def __repr__(self) -> str:
        if self._global_shift == 0:
            return 'cirq_iqm.XYGate({})'.format(proper_repr(self._exponent))
        return (
            'cirq_iqm.XYGate(exponent={}, '
            'global_shift={!r})'
        ).format(proper_repr(self._exponent), self._global_shift)
