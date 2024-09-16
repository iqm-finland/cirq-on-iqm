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
Demonstrates transforming a quantum circuit into the native gateset and connectivity of a given
IQM device, optimizing it, and then executing it on a simulator.
"""
from __future__ import annotations

from typing import Optional

import cirq
import cirq.linalg
import numpy as np

from iqm.cirq_iqm import IQMDevice
from iqm.cirq_iqm.optimizers import simplify_circuit

np.set_printoptions(precision=3)


def get_measurements(circuit: cirq.Circuit) -> list[tuple[int, cirq.GateOperation]]:
    """Find all measurements in a circuit.

    Args:
        circuit: quantum circuit

    Returns:
        tuples of (moment index, measurement operation)
    """
    if not circuit.are_all_measurements_terminal():
        raise ValueError('Non-terminal measurements are not supported')

    return [(m[0], m[1]) for m in circuit.findall_operations_with_gate_type(cirq.MeasurementGate)]


def get_qubit_order(circuit: cirq.Circuit) -> tuple[list[cirq.Qid], int]:
    """Ordering for the qubits based on lexical ordering of measurements in the circuit.

    Args:
        circuit: quantum circuit

    Returns:
        qubit order, number of measured qubits
    """
    measurements = get_measurements(circuit)

    # mapping from (key, index) to measured qubit, in lexical order
    m_qubits = {(op.gate.key, index): qubit for _, op in measurements for index, qubit in enumerate(op.qubits)}
    m_qubits = dict(sorted(m_qubits.items()))

    qubit_order = list(m_qubits.values())
    assert len(set(qubit_order)) == len(qubit_order)  # no qubit measured more than once

    # add unobserved qubits to the order
    all_qubits = set(circuit.all_qubits())
    qubit_order += sorted(all_qubits - set(qubit_order))
    return qubit_order, len(m_qubits)


def simulate_measurement_probabilities(
    sim: cirq.Simulator,
    circuit: cirq.Circuit,
) -> tuple[dict[tuple, float], list[str]]:
    """Simulate the probabilities of obtaining different measurement results in the given circuit.

    Args:
        sim: simulator
        circuit: quantum circuit

    Returns:
        map from result to its probability, measurement keys
    """
    measurements = get_measurements(circuit)
    if not measurements:
        raise ValueError('Circuit has no measurements.')

    qubit_order, n_measured_qubits = get_qubit_order(circuit)

    stripped = circuit.copy()
    stripped.batch_remove(measurements)

    # compute the state vector
    result = sim.simulate(stripped, qubit_order=qubit_order)
    state = result.state_vector()

    # trace out non-measured qubits, compute the probabilities of the various measurement outcomes
    mixture = cirq.linalg.partial_trace_of_state_vector_as_mixture(state, keep_indices=range(n_measured_qubits))
    _temp = [p * np.abs(ket) ** 2 for p, ket in mixture]
    probs = np.sum(_temp, axis=0)

    # list the all the measurement outcomes in the matching order
    measurement_arities = {op.gate.key: len(op.qubits) for _, op in measurements}
    measurement_arities = dict(sorted(measurement_arities.items()))

    shape = np.array(2) ** list(measurement_arities.values())
    outcomes = [tuple(seq) for seq in np.array(np.unravel_index(range(len(probs)), shape)).T]
    assert len(outcomes) == len(probs)

    probabilities = dict(zip(outcomes, probs))
    print('    ', probabilities)
    return probabilities, list(measurement_arities.keys())


def simulate_without_measurements(
    sim: cirq.Simulator,
    circuit: cirq.Circuit,
) -> np.ndarray:
    """Simulates given quantum circuit without its measurement operations.

    Args:
        sim: simulator
        circuit: quantum circuit

    Returns:
        state vector
    """
    measurements = get_measurements(circuit)
    stripped = circuit.copy()
    stripped.batch_remove(measurements)

    qubit_order, _ = get_qubit_order(circuit)

    result = sim.simulate(stripped, qubit_order=qubit_order)
    state = result.state_vector()
    print('    probabilities =', np.abs(state) ** 2)
    return state


def pause() -> None:
    input('\npress enter\n')


def demo(device: IQMDevice, circuit: cirq.Circuit, *, use_qsim: bool = False) -> None:
    """Transform the given circuit to a form the given device accepts, then simulate it.

    Args:
        device: device on which to execute the quantum circuit
        circuit: quantum circuit
        use_qsim: Iff True, use the ``qsim`` circuit simulator instead of the Cirq builtin simulator.
    """
    print('Source circuit:')
    print(circuit)
    pause()

    # decompose non-native gates and simplify the circuit
    circuit_decomposed = device.decompose_circuit(circuit)
    circuit_simplified = simplify_circuit(circuit_decomposed)  # NOTE: will discard Rz:s before measurements
    print('\nSimplified circuit:')
    print(circuit_simplified)
    pause()

    # map the circuit qubits to device qubits
    circuit_mapped, initial_mapping, final_mapping = device.route_circuit(circuit_simplified)

    print('\nRouted simplified circuit:')
    print(circuit_mapped)
    pause()

    # Decompose any non-native gates which might have been
    # introduced since the last decomposition.
    circuit_transformed = device.decompose_circuit(circuit_mapped)
    print('\nFinal transformed circuit:')
    print(circuit_transformed)
    pause()

    # Initialize a ket-based simulator for evaluating the circuit
    if use_qsim:
        import qsimcirq

        sim = qsimcirq.QSimSimulator()
        print('Using qsim.')
    else:
        sim = cirq.Simulator()

    # sim.run only returns the measured values over a number of repetitions of the circuit, like a hardware QPU would
    # sim.simulate returns also the simulated state of the register

    print('\nState vector simulation')
    print('\n  Original circuit:')
    state_0 = simulate_without_measurements(sim, circuit)
    print('\n  Transformed circuit:')
    state_1 = simulate_without_measurements(sim, circuit_transformed)

    # Overlap won't be perfect due to use of simplify_circuit above, which may eliminate Rz gates
    # overlap = np.abs(np.vdot(state_0, state_1))
    # print('\noverlap = |<original|transformed>| =', overlap)
    # assert np.abs(overlap - 1.0) < 1e-6, 'Circuits are not equivalent!'

    # Basis state probabilities, however, are preserved.
    probs_0 = np.abs(state_0) ** 2
    probs_1 = np.abs(state_1) ** 2
    assert np.allclose(probs_0, probs_1), 'Circuits are not equivalent!'

    print('\nSimulated measurement probabilities:')
    print('\n  Original circuit:')
    m_probs0, keys0 = simulate_measurement_probabilities(sim, circuit)
    print('\n  Transformed circuit:')
    m_probs1, keys1 = simulate_measurement_probabilities(sim, circuit_transformed)

    assert keys0 == keys1, 'Key order is not the same!'
    print(f'\nOrder of measurement keys: {keys0}')

    # Simulated measurement probabilities are also preserved,
    assert np.allclose(list(m_probs0.values()), list(m_probs1.values())), 'Circuits are not equivalent!'

    # and they are equivalent with the basis state probabilities when every qubit is measured.
    if len(m_probs0) == len(probs_0):
        assert np.allclose(list(m_probs0.values()), probs_0), 'Simulation methods are not equivalent!'

    # Random sampling of the circuit returns data that follows the measurement probabilities.
    samples_0 = sim.run(circuit, repetitions=10000)
    samples_1 = sim.run(circuit_transformed, repetitions=10000)
    # compute sorted histograms of the samples, where order of the bits in the bitstring is determined
    # by the order of the corresponding measurement keys
    hist_0 = dict(sorted(samples_0.multi_measurement_histogram(keys=keys0).items()))
    hist_1 = dict(sorted(samples_1.multi_measurement_histogram(keys=keys0).items()))

    print('\nRandom sampling:')
    print('\n  Original circuit:')
    print('    ', hist_0)
    print('\n  Transformed circuit:')
    print('    ', hist_1)
