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

"""Testing the IQM native gate definitions.
"""
# pylint: disable=redefined-outer-name,no-self-use
import cirq
import numpy as np
import pytest

import cirq_iqm.iqm_gates as ig


class TestGates:
    """Verifies that the gate definitions are correct."""

    @pytest.mark.parametrize('t', [1, 0.26, -1.32])
    def test_gate_matrices_ising(self, t):
        """Verify that the Ising gates work as expected."""

        CZ = cirq.CZPowGate(exponent=t)._unitary_()
        s = 1 - t / 2
        L = cirq.rz(-np.pi * s)._unitary_()
        assert np.allclose(np.exp(-1j * np.pi / 2 * s) * np.kron(L, L) @ ig.IsingGate(exponent=s)._unitary_(), CZ)

    @pytest.mark.parametrize('t', [1.83, 0.5, -0.5])
    def test_gate_matrices_xy(self, t):
        """Verify that the XY gates work as expected."""

        U = cirq.ISwapPowGate(exponent=t)._unitary_()
        assert np.allclose(ig.XYGate(exponent=-0.5 * t)._unitary_(), U)
