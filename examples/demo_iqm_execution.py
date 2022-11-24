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
Demonstrates executing a quantum circuit on an IQM quantum computer.

Set the IQM_SERVER_URL environment variable before running this script.
Also, if the server you are running against requires authentication, you will also have to set IQM_AUTH_SERVER,
IQM_AUTH_USERNAME and IQM_AUTH_PASSWORD.
E.g.
    export IQM_SERVER_URL="https://example.com"
    export IQM_AUTH_SERVER="https://auth.example.com"; export IQM_AUTH_USERNAME="my username";
    export IQM_AUTH_PASSWORD="my password"
"""
import os

import cirq

from cirq_iqm.devices import Adonis
from cirq_iqm.iqm_sampler import IQMSampler


def demo_adonis_run():
    """
    Run a quantum circuit on an Adonis quantum computer.
    """
    a = cirq.NamedQubit('Alice')
    b = cirq.NamedQubit('Bob')

    circuit = cirq.Circuit(cirq.X(a) ** 0.5, cirq.Z(a), cirq.measure(a, b, key='result'))

    device = Adonis()
    circuit_decomposed = device.decompose_circuit(circuit)
    print(circuit_decomposed)

    sampler = IQMSampler(os.environ['IQM_SERVER_URL'], device)

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
