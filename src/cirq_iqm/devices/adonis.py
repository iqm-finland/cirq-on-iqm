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
IQM's Adonis quantum architecture.
"""
from __future__ import annotations

from .iqm_device import IQMDevice, IQMDeviceMetadata


class Adonis(IQMDevice):
    """IQM's five-qubit transmon device.

    The qubits are connected thus::

            QB1
             |
      QB2 - QB3 - QB4
             |
            QB5

    where the lines denote which qubit pairs can be subject to two-qubit gates.

    Each qubit can be rotated about any axis in the xy plane by an arbitrary angle.
    Adonis thus has native PhasedXPowGate, XPowGate, and YPowGate gates. The two-qubit gate CZ is
    native, as well. The qubits can be measured simultaneously or separately once, at the end of
    the circuit.
    """

    def __init__(self):
        qubit_count = 5
        connectivity = ({1, 3}, {2, 3}, {4, 3}, {5, 3})
        super().__init__(IQMDeviceMetadata.from_qubit_indices(qubit_count, connectivity))
