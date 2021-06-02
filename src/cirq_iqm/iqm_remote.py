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
Circuit sampler that executes quantum circuits on the IQM backend.
"""
from __future__ import annotations

import json
import os
from typing import Any

import cirq
import numpy as np
from cirq import study
from cirq.study import resolver
from cirq_iqm.iqm_client import CircuitDTO, InstructionDTO, IQMBackendClient


def _serialize_iqm(circuit: cirq.Circuit) -> CircuitDTO:
    """Serializes a quantum circuit into the IQM data transfer format.

    Args:
        circuit: quantum circuit to serialize

    Returns:
        data transfer object representing the circuit
    """
    instructions = []
    for moment in circuit.moments:
        for operation in moment.operations:
            gate_dict = operation.gate._json_dict_()
            instructions.append(
                InstructionDTO(
                    name=gate_dict['cirq_type'],
                    qubits=[str(qubit) for qubit in operation.qubits],
                    args={key: val for key, val in gate_dict.items() if key != 'cirq_type'}
                )
            )

    circuit_dict = CircuitDTO(
        name='Serialized from Cirq',
        instructions=instructions,
        args={}  # todo: implement arguments
    )
    return circuit_dict


class IQMSampler(cirq.work.Sampler):
    """Circuit sampler for evaluating quantum circuits on IQM quantum devices.

    Args:
        url: Endpoint for accessing the device. Has to start with http or https.
        settings: Settings for the quantum hardware.
    """

    def __init__(self, url: str, settings: str):
        self._client = IQMBackendClient(url, settings=json.loads(settings))

    def run_sweep(
            self,
            program: cirq.Circuit,
            params: cirq.Sweepable,
            repetitions: int = 1,
    ) -> list[cirq.Result]:
        """Samples from the given quantum circuit.

        Nontrivial sweeping is not yet supported, ``params`` should be ``None``.

        Args:
            program: The circuit to sample from.
            params: Arguments to the program.
            repetitions: The number of times to sample (execute) the circuit.

        Returns:
            Result list for this run; one for each possible parameter
            resolver.

        Raises:
            NotImplementedError: user tried to run a nontrivial sweep
        """
        sweeps = study.to_sweeps(params or study.ParamResolver({}))
        if len(sweeps) > 1 or len(sweeps[0].keys) > 0:
            raise NotImplementedError('Sweeps are not supported')
        results = [self._send_circuit(program, repetitions=repetitions)]
        return results

    def _send_circuit(
            self,
            circuit: cirq.Circuit,
            repetitions: int = 1
    ) -> cirq.study.Result:
        """Sends the circuit to be executed by the remote IQM device.

        Args:
            circuit: quantum circuit to run
            repetitions: number of times the circuit is sampled/run

        Returns:
            results of the run

        Raises:
            CircuitExecutionException: something went wrong on the server side
            APITimeoutError: server did not return the results in the allocated time
        """
        iqm_circuit = _serialize_iqm(circuit)
        job_id = self._client.submit_circuit(circuit=iqm_circuit, shots=repetitions)
        results = self._client.wait_for_results(job_id)
        measurements = {k: np.array(v) for k, v in results.measurements.items()}
        return study.Result(params=resolver.ParamResolver(), measurements=measurements)
