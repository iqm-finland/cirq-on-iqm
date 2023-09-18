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
Also, if the server you are running against requires authentication you will also have to set
IQM_AUTH_SERVER, and either IQM_TOKENS_FILE or both of IQM_AUTH_USERNAME and IQM_AUTH_PASSWORD.

E.g.

    export IQM_SERVER_URL="https://example.com/cocos"
    export IQM_AUTH_SERVER="https://example.com/auth"
    export IQM_TOKENS_FILE="/path/to/my/tokens.json"
"""
import os

import cirq
import numpy as np

from iqm.cirq_iqm.iqm_sampler import IQMSampler
from iqm.cirq_iqm.optimizers import simplify_circuit


def fold_func(x: np.ndarray) -> str:
    """Fold the measured bit arrays into strings."""
    return ''.join(map(lambda x: chr(x + ord('0')), x))


def demo_run_circuit() -> None:
    """
    Run a quantum circuit on an IQM quantum computer.
    """
    a = cirq.NamedQubit('Alice')
    b = cirq.NamedQubit('Bob')
    circuit = cirq.Circuit(cirq.H(a), cirq.CX(a, b), cirq.measure(a, b, key='m'))
    print('Original circuit:\n')
    print(circuit)

    sampler = IQMSampler(os.environ['IQM_SERVER_URL'])

    circuit_decomposed = sampler.device.decompose_circuit(circuit)
    circuit_routed, _, _ = sampler.device.route_circuit(circuit_decomposed)
    circuit = simplify_circuit(circuit_routed)
    print('\nTranspiled and routed circuit:\n')
    print(circuit)
    print('\n')

    # This will send the circuit to the server to be run, and return a cirq.study.Result
    # containing the measurement results.
    results = sampler.run(circuit, repetitions=1000)

    # Sampler results can be accessed several ways
    # For instance, to see the histogram of results
    print(results.histogram(key='m', fold_func=fold_func))

    # Or the data itself
    print(results.data)


if __name__ == '__main__':
    demo_run_circuit()
