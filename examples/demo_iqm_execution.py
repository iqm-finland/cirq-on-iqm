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
Demonstrates executing a quantum circuit on an IQM quantum computer.

Set the IQM_SERVER_URL and IQM_SETTINGS_PATH environment variables before running this script.
E.g. export IQM_SERVER_URL="https://example.com"; export IQM_SETTINGS_PATH="/path/to/file"
"""
import os

import cirq

from cirq_iqm.adonis import Adonis
from cirq_iqm.iqm_remote import IQMSampler


def demo_adonis_run():
    """
    Run a quantum circuit on an Adonis quantum computer.
    """
    a = cirq.NamedQubit('Alice')
    b = cirq.NamedQubit('Bob')
    circuit = cirq.Circuit(
        cirq.X(a) ** 0.5,
        cirq.measure(a, b, key='result')
    )

    # map the logical qubits used in the circuit to the device qubits
    qubit_mapping = {a.name: 'QB1', b.name: 'QB2'}

    device = Adonis()
    circuit_decomposed = device.decompose_circuit(circuit)
    print(circuit_decomposed)

    with open(os.environ['IQM_SETTINGS_PATH'], 'r') as settings:
        sampler = IQMSampler(os.environ['IQM_SERVER_URL'], settings.read(), device, qubit_mapping)

    # This will send the circuit to the server to be run, and return a cirq.study.Result
    # containing the measurement results.
    results = sampler.run(circuit_decomposed, repetitions=1000)

    # Sampler results can be accessed several ways

    # For instance, to see the histogram of results
    print(results.histogram(key='result'))

    # Or the data itself
    print(results.data)


if __name__ == '__main__':
    demo_adonis_run()
