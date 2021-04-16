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
Demonstrates calling an IQM device.
"""

# https://quantumai.google/cirq/tutorials/ionq/getting_started
# https://quantumai.google/cirq/devices

from cirq_iqm.adonis import Adonis
import cirq
from cirq_iqm.iqm_device import IQMQubit
import cirq_iqm.hardware
from cirq_iqm.valkmusa import Valkmusa
from cirq_iqm.extended_qasm_parser import circuit_from_qasm
from cirq_iqm import hardware

qubit = IQMQubit(1)
circuit = cirq.Circuit(
    cirq.X(qubit)**0.5,                 # Square root of NOT.
    cirq.measure(qubit, key='result')   # Measurement.
)


qasm_program = """
        OPENQASM 2.0;
        include "qelib1.inc";
        qreg q[3];
        creg meas[3];
        U(0.2, 0.5, 1.7) q[1];
        h q[0];
        cx q[2], q[1];
        ising(-0.6) q[0], q[2];  // QASM extension
    """
circuit = circuit_from_qasm(qasm_program)
device = Adonis()
circuit_adonis = device.map_circuit(circuit)

sampler = hardware.get_sampler()
# This will run the circuit and return the results in a 'Result'
results = sampler.run(circuit_adonis, repetitions=1000)

# Sampler results can be accessed several ways

# For instance, to see the histogram of results
print(results.histogram(key='result'))

# Or the data itself
print(results.data)
