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
from cirq import Circuit, PhasedXPowGate, XPowGate, YPowGate

from iqm import iqm_client
from iqm.cirq_iqm.iqm_operation_mapping import (Instruction, instruction_to_operation,
                                                map_operation, OperationNotSupportedError)


def serialize_circuit(circuit: Circuit) -> iqm_client.Circuit:
    """Serializes a quantum circuit into the IQM data transfer format.

    Args:
        circuit: quantum circuit to serialize

    Returns:
        data transfer object representing the circuit
    """
    total_ops_list = [op for moment in circuit for op in moment]
    instructions = list(map(map_operation,total_ops_list))
    for idx,op in enumerate(total_ops_list):
        if isinstance(op, cirq.ClassicallyControlledOperation):
            if isinstance(op._sub_operation.gate, PhasedXPowGate):
                instruction = Instruction(
                    name='cc_prx',
                    qubits= op.qubits,
                    args = {'phase_t': op.gate.phase_exponent / 2,
                            }
            )
            if isinstance(op._sub_operation.gate, XPowGate):
                instruction = Instruction(
                    name='cc_prx',
                    qubits=op.qubits,
                    args={'phase_t': 0,
                          }
                )
            if isinstance(op._sub_operation.gate, YPowGate):
                instruction = Instruction(
                    name='cc_prx',
                    qubits=op.qubits,
                    args={'phase_t': 0.25,
                          }
                )
            feedback_key = op._conditions[0].keys[0].__str__()
            instruction.args['angle_t'] = op._sub_operation.gate.exponent/2
            instruction.args['feedback_key': feedback_key]
            measurement_already_used = False #flags if multiple measurements have the same key
            for i in instructions:
                if i.name == "measure" and i.args["key"] == feedback_key:
                    if measurement_already_used: #raise error if measurement has already been used as condition
                        raise OperationNotSupportedError("Measurement condition for cc_prx must only be from one qubit")
                    measurement_already_used=True #change the flag to True now that measurement is used
                    if len(i.qubits) > 1:
                        raise OperationNotSupportedError("Measurement condition for cc_prx must only be from one qubit")
                    instruction.args['feedback_qubit'] = i.qubits[0]
        instructions.insert(idx, instruction)
    return iqm_client.Circuit(name='Serialized from Cirq', instructions=instructions)


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
