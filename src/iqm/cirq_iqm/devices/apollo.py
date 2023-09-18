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
IQM's Apollo quantum architecture.
"""
from __future__ import annotations

from .iqm_device import IQMDevice, IQMDeviceMetadata


class Apollo(IQMDevice):
    r"""IQM's twenty-qubit transmon device.

    The qubits are connected thus::

            QB20  QB17
            /  \  /  \
         QB19  QB16  QB12
         /  \  /  \  /  \
      QB18  QB15  QB11  QB7
         \  /  \  /  \  /
         QB14  QB10  QB6
         /  \  /  \  /
      QB13  QB9   QB5
         \  /  \  /  \
         QB8   QB4   QB2
            \  /  \  /
            QB3   QB1

    where the lines denote which qubit pairs can be subject to two-qubit gates.

    Each qubit can be rotated about any axis in the xy plane by an arbitrary angle.
    Apollo thus has native PhasedXPowGate, XPowGate, and YPowGate gates. The two-qubit gate CZ is
    native, as well. The qubits can be measured simultaneously or separately once, at the end of
    the circuit.
    """

    def __init__(self):
        qubit_count = 20
        connectivity = (
            {1, 2},
            {1, 4},
            {2, 5},
            {3, 4},
            {3, 8},
            {4, 5},
            {4, 9},
            {5, 6},
            {5, 10},
            {6, 7},
            {6, 11},
            {7, 12},
            {8, 9},
            {8, 13},
            {9, 10},
            {9, 14},
            {10, 11},
            {10, 15},
            {11, 12},
            {11, 16},
            {12, 17},
            {13, 14},
            {14, 15},
            {14, 18},
            {15, 16},
            {15, 19},
            {16, 17},
            {16, 20},
            {18, 19},
            {19, 20},
        )
        super().__init__(IQMDeviceMetadata.from_qubit_indices(qubit_count, connectivity))
