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

from cirq import Circuit, ClassicallyControlledOperation

from iqm import iqm_client
from iqm.cirq_iqm.iqm_operation_mapping import OperationNotSupportedError, instruction_to_operation, map_operation


def serialize_circuit(circuit: Circuit) -> iqm_client.Circuit:
    """Serializes a quantum circuit into the IQM data transfer format.

    Args:
        circuit: quantum circuit to serialize

    Returns:
        data transfer object representing the circuit
    """
    total_ops_list = []
    cc_prx_support = False
    for moment in circuit:
        for op in moment:
            if isinstance(op, ClassicallyControlledOperation):
                cc_prx_support = True
            total_ops_list.append(op)
    instructions = list(map(map_operation, total_ops_list))

    if cc_prx_support:
        measurement_dict = {}
        cc_prx_dict = {}

        for idx, inst in enumerate(instructions):
            if inst.name == "cc_prx":
                cc_prx_dict[inst] = idx
            if inst.name == "measure":
                measurement_dict[inst.args["key"]] = (inst.qubits, idx)

        for op, idx in cc_prx_dict.items():
            m_idx = measurement_dict[op.args["feedback_key"]][1]
            feedback_qubit = measurement_dict[op.args["feedback_key"]][0][0]
            if len(feedback_qubit) > 1:
                raise OperationNotSupportedError("Measurement condition for cc_prx must only be from one qubit")
            if idx < m_idx:
                raise OperationNotSupportedError("Measurement condition must precede cc_prx operation")
            op.args["feedback_qubit"] = feedback_qubit[0]

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
