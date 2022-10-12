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
import cirq
from cirq import CZPowGate, GateOperation, MeasurementGate, PhasedXPowGate, XPowGate, YPowGate, ZPowGate
from iqm_client.iqm_client import Instruction
import pytest

from cirq_iqm.iqm_operation_mapping import OperationNotSupportedError, map_operation


@pytest.fixture()
def qubit_1() -> cirq.NamedQubit:
    return cirq.NamedQubit('QB1')


@pytest.fixture()
def qubit_2() -> cirq.NamedQubit:
    return cirq.NamedQubit('QB2')


def test_raises_error_for_unsupported_operation(qubit_1):
    operation = GateOperation(ZPowGate(), [qubit_1])
    with pytest.raises(OperationNotSupportedError):
        map_operation(operation)


def test_maps_measurement_gate(qubit_1):
    key = 'test measurement'
    operation = GateOperation(MeasurementGate(1, key), [qubit_1])
    mapped = map_operation(operation)
    expected = Instruction(name='measurement', qubits=(str(qubit_1),), args={'key': key})
    assert expected == mapped


@pytest.mark.parametrize(
    'gate, expected_angle, expected_phase',
    [
        (XPowGate(exponent=0.5), 0.25, 0),
        (YPowGate(exponent=0.75), 0.375, 0.25),
        (PhasedXPowGate(exponent=0.25, phase_exponent=0.5), 0.125, 0.25),
    ],
)
def test_maps_to_phased_rx(qubit_1, gate, expected_angle, expected_phase):
    operation = GateOperation(gate, [qubit_1])
    mapped = map_operation(operation)
    assert mapped.name == 'phased_rx'
    assert mapped.qubits == (str(qubit_1),)
    # The unit for angle and phase is full turns
    assert mapped.args['angle_t'] == expected_angle
    assert mapped.args['phase_t'] == expected_phase


def test_maps_cz_gate(qubit_1, qubit_2):
    operation = GateOperation(CZPowGate(), [qubit_1, qubit_2])
    mapped = map_operation(operation)
    expected = Instruction(name='cz', qubits=(str(qubit_1), str(qubit_2)), args={})
    assert expected == mapped


def test_raises_error_for_general_cz_pow_gate(qubit_1, qubit_2):
    operation = GateOperation(CZPowGate(exponent=0.5), [qubit_1, qubit_2])
    with pytest.raises(OperationNotSupportedError):
        map_operation(operation)


def test_raises_error_for_non_trivial_invert_mask(qubit_1, qubit_2):
    operation = GateOperation(MeasurementGate(2, 'measurement key', invert_mask=(True, False)), [qubit_1, qubit_2])
    with pytest.raises(OperationNotSupportedError):
        map_operation(operation)
