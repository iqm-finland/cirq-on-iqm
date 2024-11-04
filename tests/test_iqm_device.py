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
from cirq import Circuit, HardCodedInitialMapper, NamedQid, NamedQubit, ops
from cirq.testing import assert_circuits_have_same_unitary_given_final_permutation, assert_has_diagram, random_circuit
import pytest

from iqm.cirq_iqm import Adonis, Apollo, IQMDevice, IQMMoveGate


def test_equality_method():
    adonis_1 = Adonis()
    adonis_2 = Adonis()
    adonis_3 = Adonis()
    apollo_1 = Apollo()
    apollo_2 = Apollo()
    adonis_3._metadata = apollo_1.metadata

    assert adonis_1 == adonis_2
    assert apollo_1 == apollo_2
    assert adonis_2 != adonis_3


def test_device_without_resonator(device_without_resonator):
    assert_qubit_indexing(
        device_without_resonator,
        set(zip(range(1, len(device_without_resonator.qubits) + 1), device_without_resonator.qubits)),
    )
    assert len(device_without_resonator.resonators) == 0


def test_device_with_resonator(device_with_resonator):
    print(device_with_resonator.qubits)
    # Tests for device with resonator should pass too.
    assert_qubit_indexing(
        device_with_resonator, set(zip(range(1, len(device_with_resonator.qubits) + 1), device_with_resonator.qubits))
    )
    assert len(device_with_resonator.resonators) == 1
    assert device_with_resonator.resonators[0] == NamedQid(
        "COMP_R", device_with_resonator._metadata.RESONATOR_DIMENSION
    )


def assert_qubit_indexing(backend: IQMDevice, correct_idx_name_associations):
    assert all(backend.get_qubit(idx) == name for idx, name in correct_idx_name_associations)
    assert all(backend.get_qubit_index(name) == idx for idx, name in correct_idx_name_associations)
    # Below assertions are done in Qiskit but do not make sense for Cirq.
    # assert backend.index_to_qubit_name(7) is None
    # assert backend.qubit_name_to_index("Alice") is None


@pytest.mark.parametrize("device", ["device_without_resonator", "device_with_resonator", Apollo(), Adonis()])
def test_transpilation(device: IQMDevice, request):
    if isinstance(device, str):
        device = request.getfixturevalue(device)
    print(device)
    size = 5
    circuit = random_circuit(device.qubits[:size], size, 1, random_state=1337)
    print(circuit)
    print("decomposing")
    decomposed_circuit = device.decompose_circuit(circuit)
    naive_map = {q: q for q in device.qubits}
    print("routing")
    routed_circuit, initial_map, final_map = device.route_circuit(
        decomposed_circuit, initial_mapper=HardCodedInitialMapper(naive_map)
    )
    assert initial_map == naive_map
    print("decomposing")
    decomposed_routed_circuit = device.decompose_circuit(routed_circuit)
    print("validating")
    device.validate_circuit(decomposed_routed_circuit)
    print("checking equivalence")
    qubit_map = {q1: q2 for q1, q2 in final_map.items() if q1 in decomposed_routed_circuit.all_qubits()}
    assert_circuits_have_same_unitary_given_final_permutation(
        decomposed_circuit, circuit, qubit_map={q: q for q in device.qubits[:size]}
    )
    print("Circuit qubits:", circuit.all_qubits())
    print("Routed circuit qubits:", routed_circuit.all_qubits())
    for q in routed_circuit.all_qubits():
        if q not in circuit.all_qubits():
            circuit.append(ops.IdentityGate(1)(q))
    print("Circuit qubits after adding routing qubits:", circuit.all_qubits())
    assert_circuits_have_same_unitary_given_final_permutation(routed_circuit, circuit, qubit_map=qubit_map)
    assert_circuits_have_same_unitary_given_final_permutation(decomposed_routed_circuit, circuit, qubit_map=qubit_map)
    if device.metadata.architecture is not None:
        assert routed_circuit.iqm_calibration_set_id == device.metadata.architecture.calibration_set_id  # type: ignore
        assert (
            decomposed_routed_circuit.iqm_calibration_set_id  # type: ignore
            == device.metadata.architecture.calibration_set_id
        )
    else:
        assert routed_circuit.iqm_calibration_set_id is None  # type: ignore
        assert decomposed_routed_circuit.iqm_calibration_set_id is None  # type: ignore


@pytest.mark.parametrize(
    "device",
    ["device_without_resonator", "device_with_resonator", Apollo(), Adonis(), "device_with_multiple_resonators"],
)
def test_qubit_connectivity(device: IQMDevice, request):
    if isinstance(device, str):
        device = request.getfixturevalue(device)
    for edge in [(q1, q2) for q1 in device.qubits for q2 in device.qubits if q1 != q2]:
        gate = ops.CZPowGate()(*edge)
        if (
            edge in device.supported_operations[ops.CZPowGate]
            or tuple(reversed(edge)) in device.supported_operations[ops.CZPowGate]
        ):
            device.check_qubit_connectivity(gate)  # This should not raise an error
        else:
            with pytest.raises(ValueError):
                device.check_qubit_connectivity(gate)
        with pytest.raises(ValueError):
            device.check_qubit_connectivity(ops.SwapPowGate()(*edge))


def test_validate_moves(device_with_resonator):
    # Test valid MOVE sandwich
    circuit = Circuit(
        IQMMoveGate()(device_with_resonator.qubits[0], device_with_resonator.resonators[0]),
        IQMMoveGate()(device_with_resonator.qubits[0], device_with_resonator.resonators[0]),
    )
    assert device_with_resonator.validate_moves(circuit) is None
    # Test invalid MOVE sandwich
    circuit = Circuit(
        IQMMoveGate()(device_with_resonator.qubits[0], device_with_resonator.resonators[0]),
        IQMMoveGate()(device_with_resonator.qubits[1], device_with_resonator.resonators[0]),
    )
    with pytest.raises(ValueError):
        device_with_resonator.validate_moves(circuit)

    circuit = Circuit(
        IQMMoveGate()(device_with_resonator.qubits[0], device_with_resonator.resonators[0]),
        IQMMoveGate()(device_with_resonator.qubits[0], device_with_resonator.qubits[1]),
    )
    with pytest.raises(ValueError):
        device_with_resonator.validate_moves(circuit)

    circuit = Circuit(
        IQMMoveGate()(device_with_resonator.resonators[0], device_with_resonator.qubits[1]),
        IQMMoveGate()(device_with_resonator.resonators[0], device_with_resonator.qubits[1]),
    )
    with pytest.raises(ValueError):
        device_with_resonator.validate_moves(circuit)

    # Test valid MOVE without sandwich
    circuit = Circuit(
        IQMMoveGate()(device_with_resonator.qubits[0], device_with_resonator.resonators[0]),
    )
    with pytest.raises(ValueError):
        device_with_resonator.validate_moves(circuit)

    # Test odd valid MOVEs (incomplete sandwich)
    circuit = Circuit(
        IQMMoveGate()(device_with_resonator.qubits[0], device_with_resonator.resonators[0]),
        IQMMoveGate()(device_with_resonator.qubits[0], device_with_resonator.resonators[0]),
        IQMMoveGate()(device_with_resonator.qubits[0], device_with_resonator.resonators[0]),
    )
    with pytest.raises(ValueError):
        device_with_resonator.validate_moves(circuit)
    # Test no moves
    circuit = Circuit()
    assert device_with_resonator.validate_moves(circuit) is None
    assert (
        device_with_resonator.validate_move(
            ops.CZPowGate()(device_with_resonator.qubits[0], device_with_resonator.resonators[0])
        )
        is None
    )


def test_move_gate_drawing():
    """Check that the MOVE gate can be drawn."""
    res = NamedQid("Resonator", dimension=2)
    qubit = NamedQubit("Qubit")
    gate = IQMMoveGate()(qubit, res)
    c = Circuit(gate)
    assert_has_diagram(c, "Qubit: ─────────────MOVE(QB)────\n                    │\nResonator (d=2): ───MOVE(Res)───")

    assert str(gate) == "MOVE(Qubit, Resonator (d=2))"
