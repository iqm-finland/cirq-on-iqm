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

"""
Demonstrates transforming a quantum circuit into the native gateset and connectivity of a given
IQM device, optimizing it, and then executing it on a simulator.
"""
import cirq
import numpy as np

np.set_printoptions(precision=3)


def demo(device, circuit_original, do_measure, *, use_qsim=False):
    """Tranform the given circuit to a form the given device accepts, then simulate it.

    Args:
        device (IQMDevice): device on which to execute the quantum circuit
        circuit_original (cirq.Circuit): quantum circuit
        do_measure (bool): Iff True, ``circuit_original`` contains measurements, in which case the
            state after the circuit is not simulated, just the measurement results.
        use_qsim (bool): Iff True, use the ``qsim`` circuit simulator instead of the Cirq builtin simulator.
    """
    print('Source circuit:')
    print(circuit_original)
    print()

    # construct a new quantum circuit respecting Adonis' properties
    circuit_transformed = device.map_circuit(circuit_original)
    print('Decomposed circuit:')
    print(circuit_transformed)
    print()

    # clean up the circuit (in place)
    device.simplify_circuit(circuit_transformed)
    print('Simplified circuit:')
    print(circuit_transformed)
    print()

    # Initialize a ket-based simulator for evaluating the circuit
    if use_qsim:
        import qsimcirq
        sim = qsimcirq.QSimSimulator()
        print('Using qsim.')
    else:
        sim = cirq.Simulator()

    # sim.run only returns the measured values over a number of repetitions of the circuit, like a hardware QPU would
    # sim.simulate returns also the simulated state of the register

    if not do_measure:
        result_transformed = sim.simulate(circuit_transformed)  # qubit_order=...
        print('\nSimulate the transformed circuit:')
        print('result =', result_transformed)
        print('probabilities =', np.abs(result_transformed.state_vector()) ** 2)

        result_original = sim.simulate(circuit_original)  # qubit_order=...
        print('\nSimulate the original circuit:')
        print('result =', result_original)
        overlap = np.abs(np.vdot(result_original.state_vector(), result_transformed.state_vector()))
        print('\noverlap = |<original|transformed>| =', overlap)
        assert np.abs(overlap - 1.0) < 1e-6, 'Circuits are not equivalent!'
    else:
        samples_transformed = sim.run(circuit_transformed, repetitions=10000)
        samples_original = sim.run(circuit_original, repetitions=10000)

        # Print a histogram of results
        # the counter interprets a multiqubit measurement result as a bit string, and converts it into an integer
        key = 'meas_1'
        print('\nSample the transformed circuit:')
        print(samples_transformed.histogram(key=key))
        print('\nSample the original circuit:')
        print(samples_original.histogram(key=key))
