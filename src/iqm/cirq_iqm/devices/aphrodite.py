# Copyright 2020–2025 Cirq on IQM developers
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
IQM's Aphrodite quantum architecture.
"""
from __future__ import annotations

from .iqm_device import IQMDevice, IQMDeviceMetadata


class Aphrodite(IQMDevice):
    r"""IQM's 54-qubit transmon device.

    The qubits are connected thus::

          QB54  QB51  QB46  QB39
          /  \  /  \  /  \  /  \
       QB53  QB50  QB45  QB38  QB31
       /  \  /  \  /  \  /  \  /
    QB52  QB49  QB44  QB37  QB30
       \  /  \  /  \  /  \  /  \
       QB48  QB43  QB36  QB29  QB22
       /  \  /  \  /  \  /  \  /  \
    QB47  QB42  QB35  QB28  QB21  QB14
       \  /  \  /  \  /  \  /  \  /
       QB41  QB34  QB27  QB20  QB13
       /  \  /  \  /  \  /  \  /  \
    QB40  QB33  QB26  QB19  QB12  QB7
       \  /  \  /  \  /  \  /  \  /
       QB32  QB25  QB18  QB11  QB6
          \  /  \  /  \  /  \  /  \
          QB24  QB17  QB10  QB5   QB2
          /  \  /  \  /  \  /  \  /
       QB23  QB16  QB9   QB4   QB1
          \  /  \  /  \  /
          QB15  QB8   QB3

    where the lines denote which qubit pairs can be subject to two-qubit gates.

    Aphrodite has native PhasedXPowGate, XPowGate, and YPowGate gates. The two-qubit gate CZ is
    native, as well. The qubits can be measured simultaneously or separately any number of times.
    """
    def __init__(self):
        qubit_count = 54
        connectivity = (
            {1, 2},
            {1, 5},
            {2, 6},
            {3, 4},
            {3, 9},
            {4, 5},
            {4, 10},
            {5, 6},
            {5, 11},
            {6, 7},
            {6, 12},
            {7, 13},
            {8, 9},
            {8, 16},
            {9, 10},
            {9, 17},
            {10, 11},
            {10, 18},
            {11, 12},
            {11, 19},
            {12, 13},
            {12, 20},
            {13, 14},
            {13, 21},
            {14, 22},
            {15, 16},
            {15, 23},
            {16, 17},
            {16, 24},
            {17, 18},
            {17, 25},
            {18, 19},
            {18, 26},
            {19, 20},
            {19, 27},
            {20, 21},
            {20, 28},
            {21, 22},
            {21, 29},
            {22, 30},
            {23, 24},
            {24, 25},
            {24, 32},
            {25, 26},
            {25, 33},
            {26, 27},
            {26, 34},
            {27, 28},
            {27, 35},
            {28, 29},
            {28, 36},
            {29, 30},
            {29, 37},
            {30, 31},
            {30, 38},
            {31, 39},
            {32, 33},
            {32, 40},
            {33, 34},
            {33, 41},
            {34, 35},
            {34, 42},
            {35, 36},
            {35, 43},
            {36, 37},
            {36, 44},
            {37, 38},
            {37, 45},
            {38, 39},
            {38, 46},
            {40, 41},
            {41, 42},
            {41, 47},
            {42, 43},
            {42, 48},
            {43, 44},
            {43, 49},
            {44, 45},
            {44, 50},
            {45, 46},
            {45, 51},
            {47, 48},
            {48, 49},
            {48, 52},
            {49, 50},
            {49, 53},
            {50, 51},
            {50, 54},
            {52, 53},
            {53, 54},
        )
        super().__init__(IQMDeviceMetadata.from_qubit_indices(qubit_count, connectivity))
