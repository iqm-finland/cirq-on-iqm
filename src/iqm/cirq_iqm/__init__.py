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
"""Types for representing and methods for manipulating operations on IQM's quantum computers."""
from importlib.metadata import PackageNotFoundError, version
import warnings

from .devices import *
from .extended_qasm_parser import circuit_from_qasm

try:
    DIST_NAME = 'cirq-iqm'
    __version__ = version(DIST_NAME)
except PackageNotFoundError:
    __version__ = 'unknown'
finally:
    del version, PackageNotFoundError
# pylint: disable=wrong-import-position
from .iqm_gates import *
from .transpiler import transpile_insert_moves_into_circuit

warnings.warn(
    DeprecationWarning(
        'The cirq-iqm package is deprecated and new versions of Cirq on IQM will be published as part of '
        'iqm-client. Please uninstall cirq-iqm and install iqm-client[cirq] to get the newest version.'
    )
)
