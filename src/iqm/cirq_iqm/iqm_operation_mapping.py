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
from cirq import NamedQid
from cirq.ops import CZPowGate, Gate, MeasurementGate, Operation, PhasedXPowGate, XPowGate, YPowGate

from iqm.cirq_iqm.iqm_gates import IQMMoveGate
from iqm.iqm_client import Instruction

# Mapping from IQM operation names to cirq operations
_IQM_CIRQ_OP_MAP: dict[str, tuple[type[Gate], ...]] = {
    # XPow and YPow kept for convenience, Cirq does not know how to decompose them into PhasedX
    # so we would have to add those rules...
    'prx': (PhasedXPowGate, XPowGate, YPowGate),
    'cz': (CZPowGate,),
    'move': (IQMMoveGate,),
    'measure': (MeasurementGate,),
}


def instruction_to_operation(instr: Instruction) -> Operation:
    """Convert an IQM instruction to a Cirq Operation.

    Args:
        instr: the IQM instruction

    Returns:
        Operation: the converted operation

    Raises:
        OperationNotSupportedError When the circuit contains an unsupported operation.

    """
    if instr.name not in _IQM_CIRQ_OP_MAP:
        raise OperationNotSupportedError(f'Operation {instr.name} not supported.')

    gate_type = _IQM_CIRQ_OP_MAP[instr.name][0]
    args_map = {'angle_t': 'exponent', 'phase_t': 'phase_exponent'}
    args = {args_map[k]: v * 2 for k, v in instr.args.items() if k in args_map}
    if 'key' in instr.args.keys():
        args['key'] = instr.args['key']
        args['num_qubits'] = len(instr.qubits)
    qubits = [NamedQid(qubit, dimension=2) for qubit in instr.qubits]
    return gate_type(**args)(*qubits)


class OperationNotSupportedError(RuntimeError):
    """Raised when a given operation is not supported by the IQM server."""


def map_operation(operation: Operation) -> Instruction:
    """Map a Cirq Operation to the IQM data transfer format.

    Assumes the circuit has been transpiled so that it only contains operations natively supported by the
    given IQM quantum architecture.

    Args:
        operation: a Cirq Operation

    Returns:
        Instruction: the converted operation

    Raises:
        OperationNotSupportedError When the circuit contains an unsupported operation.

    """
    phased_rx_name = 'prx'
    qubits = [qubit.name if isinstance(qubit, NamedQid) else str(qubit) for qubit in operation.qubits]
    if isinstance(operation.gate, PhasedXPowGate):
        return Instruction(
            name=phased_rx_name,
            qubits=tuple(qubits),
            args={'angle_t': operation.gate.exponent / 2, 'phase_t': operation.gate.phase_exponent / 2},
        )
    if isinstance(operation.gate, XPowGate):
        return Instruction(
            name=phased_rx_name,
            qubits=tuple(qubits),
            args={'angle_t': operation.gate.exponent / 2, 'phase_t': 0},
        )
    if isinstance(operation.gate, YPowGate):
        return Instruction(
            name=phased_rx_name,
            qubits=tuple(qubits),
            args={'angle_t': operation.gate.exponent / 2, 'phase_t': 0.25},
        )
    if isinstance(operation.gate, MeasurementGate):
        if any(operation.gate.full_invert_mask()):
            raise OperationNotSupportedError('Invert mask not supported')

        return Instruction(
            name='measure',
            qubits=tuple(qubits),
            args={'key': operation.gate.key},
        )
    if isinstance(operation.gate, CZPowGate):
        if operation.gate.exponent == 1.0:
            return Instruction(
                name='cz',
                qubits=tuple(qubits),
                args={},
            )
        raise OperationNotSupportedError(
            f'CZPowGate exponent was {operation.gate.exponent}, but only 1 is natively supported.'
        )

    if isinstance(operation.gate, IQMMoveGate):
        return Instruction(
            name='move',
            qubits=tuple(qubits),
            args={},
        )

    raise OperationNotSupportedError(f'{type(operation.gate)} not natively supported.')
