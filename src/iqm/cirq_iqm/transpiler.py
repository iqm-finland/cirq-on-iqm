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
"""Helper functions for IQM specific transpilation needs."""
from __future__ import annotations

from typing import Optional

from cirq import Circuit

from iqm.cirq_iqm.serialize import deserialize_circuit, serialize_circuit
from iqm.iqm_client import ExistingMoveHandlingOptions, transpile_insert_moves


def transpile_insert_moves_into_circuit(
    cirq_circuit: Circuit,
    device: "IQMDevice",
    existing_moves: Optional[ExistingMoveHandlingOptions] = None,
    qubit_mapping: Optional[dict[str, str]] = None,
) -> Circuit:
    """Transpile the circuit to insert MOVE gates where needed.

    Args:
        cirq_circuit (cirq.Circuit): Circuit to transpile.
        device (IQMDevice): Device to transpile for.
        existing_moves (ExistingMoveHandlingOptions) : How to handle existing MOVE gates.
        qubit_mapping (dict[str, str]): Mapping from qubit names in the circuit to the device.

    Returns:
        cirq.Circuit: Transpiled circuit.
    """
    iqm_client_circuit = serialize_circuit(cirq_circuit)
    new_iqm_client_circuit = transpile_insert_moves(
        iqm_client_circuit,
        device.metadata.to_architecture(),
        existing_moves=existing_moves,
        qubit_mapping=qubit_mapping,
    )
    new_cirq_circuit = deserialize_circuit(new_iqm_client_circuit)
    return new_cirq_circuit
