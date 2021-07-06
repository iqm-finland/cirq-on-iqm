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
"""Tests for the qubit mapping functionality.
"""
# pylint: disable=redefined-outer-name,no-self-use
from __future__ import annotations

import cirq
import pytest

import cirq_iqm.adonis as ad
from cirq_iqm.iqm_device import IQMQubit


@pytest.fixture(scope='module')
def adonis():
    """Adonis device fixture."""
    return ad.Adonis()


class TestQubitMapping:
    """Mapping of qubit names."""

    def test_map_circuit_with_device_qubit(self, adonis):
        """Device qubits are not changed."""

        q = adonis.qubits[2]
        orig = cirq.Circuit()
        orig.append(cirq.X.on(q))

        assert orig[0].qubits == {q}

        mapped = adonis.map_circuit(orig)

        # the mapped circuit is attached to the given device
        assert mapped.device is adonis
        # qubits have not changed
        assert mapped[0].qubits == {q}


    def test_map_circuit_with_named_qubit(self, adonis):
        """Named qubits with an integer in the name can be mapped to device qubits."""

        q = cirq.NamedQubit('qubit-2')
        orig = cirq.Circuit()
        orig.append(cirq.X.on(q))

        assert orig[0].qubits == {q}

        mapped = adonis.map_circuit(orig)

        # the mapped circuit is attached to the given device
        assert mapped.device is adonis
        # qubits have been mapped to device qubits
        assert mapped[0].qubits == {IQMQubit(2)}


    def test_named_qubit_not_on_device(self, adonis):
        """If a Circuit is attached to a specific Device, only device qubits can be used in it."""

        q = cirq.NamedQubit('qubit-2')
        orig = cirq.Circuit(device=adonis)

        with pytest.raises(ValueError, match='Qubit not on device:'):
            orig.append(cirq.X.on(q))
