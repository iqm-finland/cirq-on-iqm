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
Helper functions for serializing and deserializing quantum circuits between Cirq and IQM Circuit formats.
"""

import cirq
from cirq import Circuit

from iqm import iqm_client
from iqm.cirq_iqm.iqm_operation_mapping import OperationNotSupportedError, instruction_to_operation, map_operation


def serialize_circuit(circuit: iqm_client.Circuit) -> Circuit:
    """Serializes a quantum circuit into the IQM data transfer format.

    Args:
        circuit: quantum circuit to serialize

    Returns:
        data transfer object representing the circuit
    """
    total_ops_list = [op for moment in circuit for op in moment]
    instructions = list(map(map_operation, total_ops_list))
    for idx, op in enumerate(total_ops_list):
        if isinstance(op, cirq.ClassicallyControlledOperation):
            feedback_key = str(op._conditions[0].keys[0])
            measurement_already_used = False
            for m_idx, i in enumerate(instructions):
                if i.name == "measure" and i.args["key"] == feedback_key:
                    if m_idx > idx:
                        raise OperationNotSupportedError("Measurement condition must precede cc_prx operation")
                    if measurement_already_used:  # raise error if measurement has already been used as condition
                        raise OperationNotSupportedError("Measurement condition for cc_prx must only be from one qubit")
                    measurement_already_used = True  # change the flag to True now that measurement is used
                    if len(i.qubits) > 1:
                        raise OperationNotSupportedError("Measurement condition for cc_prx must only be from one qubit")
                    feedback_qubit = i.qubits[0]
                    instructions[idx].args["feedback_key"] = feedback_key
                    instructions[idx].args["feedback_qubit"] = feedback_qubit
    return iqm_client.Circuit(name="Serialized from Cirq", instructions=instructions)


def deserialize_circuit(circuit: iqm_client.Circuit) -> Circuit:
    """Deserializes a quantum circuit from the IQM data transfer format to a Cirq Circuit.

    Args:
        circuit: data transfer object representing the circuit

    Returns:
        quantum circuit
    """
    return Circuit(
        map(
            instruction_to_operation,
            circuit.instructions,
        )
    )
