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
"""Test IQM parameterizations of certain two-qubit gate families.
"""
# pylint: disable=no-self-use
from cirq import ops
import numpy as np
import pytest

from cirq_iqm.iqm_gates import IsingGate, XYGate


R = ops.ZPowGate(exponent=0.5, global_shift=-0.5)._unitary_()  # == Rz(pi / 2)
L = np.kron(R, R)
I = np.eye(4)


@pytest.mark.parametrize('p, expected', [
    (0.5, np.exp(1j * np.pi / 4) * L @ ops.CZ._unitary_()),
    (1, 1j * L @ L),
    (2, -I),
    (4, I),
])
def test_isinggate(p, expected):
    """IsingGate should return the correct Cirq gate instance."""
    assert IsingGate(p)._unitary_() == pytest.approx(expected)

@pytest.mark.parametrize('p, expected', [
    (0.5, ops.ISWAP._unitary_().T.conj()),
    (1, -L @ L),
    (2, I),
    (4, I),
])
def test_xygate(p, expected):
    """XYGate should return the correct Cirq gate instance."""
    assert XYGate(p)._unitary_() == pytest.approx(expected)
