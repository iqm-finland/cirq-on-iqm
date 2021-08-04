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
"""Logic for mapping Cirq Operations to the IQM transfer format.
"""
from cirq.ops import Operation, PhasedXPowGate, XPowGate, YPowGate, MeasurementGate, CZPowGate
from cirq_iqm.iqm_client import InstructionDTO


class OperationNotSupportedError(RuntimeError):
    """Raised when a given operation is not supported by the data transfer format."""


def map_operation(operation: Operation) -> InstructionDTO:
    """Map a Cirq Operation to the IQM data transfer format.

    Assumes the circuit has been transpiled so that it only contains operations natively supported by the
    given IQM quantum architecture.

    Args:
        operation: a Cirq Operation

    Returns:
        InstructionDTO: the converted operation

    Raises:
        OperationNotSupportedError When the circuit contains an unsupported operation.

    """
    phased_rx_name = 'phased_rx'
    qubits = [str(qubit) for qubit in operation.qubits]
    if isinstance(operation.gate, PhasedXPowGate):
        return InstructionDTO(
            name=phased_rx_name,
            qubits=qubits,
            args={
                'angle_t': operation.gate.exponent / 2,
                'phase_t': operation.gate.phase_exponent / 2
            }
        )
    if isinstance(operation.gate, XPowGate):
        return InstructionDTO(
            name=phased_rx_name,
            qubits=qubits,
            args={'angle_t': operation.gate.exponent / 2,
                  'phase_t': 0}
        )
    if isinstance(operation.gate, YPowGate):
        return InstructionDTO(
            name=phased_rx_name,
            qubits=qubits,
            args={'angle_t': operation.gate.exponent / 2,
                  'phase_t': 0.25}
        )
    if isinstance(operation.gate, MeasurementGate):
        return InstructionDTO(
            name='measurement',
            qubits=qubits,
            args={'key': operation.gate.key}
        )
    if isinstance(operation.gate, CZPowGate):
        if operation.gate.exponent == 1.0:
            return InstructionDTO(
                name='cz',
                qubits=qubits,
                args={}
            )
        raise OperationNotSupportedError(f'CZPowGate exponent {operation.gate.exponent}, only 1 is natively supported.')

    raise OperationNotSupportedError(f'{type(operation.gate)} not natively supported.')
