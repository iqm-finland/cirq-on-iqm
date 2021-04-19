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
from cirq_iqm import iqm_remote

# todo: remove mocking when the server is deployed
import tests.coco_mock
tests.coco_mock.mock_backend()


qubit = IQMQubit(1)
circuit = cirq.Circuit(
    cirq.X(qubit) ** 0.5,  # Square root of NOT.
    cirq.measure(qubit, key='result')  # Measurement.
)

device = Adonis()
circuit_adonis = device.map_circuit(circuit)

sampler = iqm_remote.get_sampler_from_env()
# This will run the circuit and return the results in a 'Result'
results = sampler.run(circuit_adonis, repetitions=1000)

# Sampler results can be accessed several ways

# For instance, to see the histogram of results
print(results.histogram(key='result'))

# Or the data itself
print(results.data)
