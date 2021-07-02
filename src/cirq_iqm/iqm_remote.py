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
Circuit sampler that executes quantum circuits on an IQM quantum computer.
"""
from __future__ import annotations

import json

import cirq
import numpy as np
from cirq import study
from cirq.study import resolver
from cirq_iqm.iqm_client import CircuitDTO, IQMClient, SingleQubitMappingDTO
from cirq_iqm.iqm_operation_mapping import map_operation


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
            instructions.append(map_operation(operation))

    return CircuitDTO(
        name='Serialized from Cirq',
        instructions=instructions,
        args={}  # todo: implement arguments
    )


class IQMSampler(cirq.work.Sampler):
    """Circuit sampler for executing quantum circuits on IQM quantum computers.

    Args:
        url: Endpoint for accessing the server interface. Has to start with http or https.
        settings: Settings for the quantum computer.
        qubit_mapping: A dict that maps logical qubit names to physical qubit names
    """
    def __init__(self, url: str, settings: str, qubit_mapping: dict[str, str]):
        self._client = IQMClient(url, settings=json.loads(settings))
        self._qubit_mapping = [SingleQubitMappingDTO(logical_name=k, physical_name=v) for k, v in qubit_mapping.items()]

    def run_sweep(
            self,
            program: cirq.Circuit,
            params: cirq.Sweepable,
            repetitions: int = 1,
    ) -> list[cirq.Result]:
        """Sweeping is not supported yet. Use the `run` method instead.

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
            repetitions: int = 1,
    ) -> cirq.study.Result:
        """Sends the circuit to be executed.

        Args:
            circuit: quantum circuit to execute
            repetitions: number of times the circuit is sampled

        Returns:
            results of the execution

        Raises:
            CircuitExecutionError: something went wrong on the server
            APITimeoutError: server did not return the results in the allocated time
        """
        iqm_circuit = _serialize_iqm(circuit)
        job_id = self._client.submit_circuit(iqm_circuit, self._qubit_mapping, repetitions)
        results = self._client.wait_for_results(job_id)
        measurements = {k: np.array(v) for k, v in results.measurements.items()}
        return study.Result(params=resolver.ParamResolver(), measurements=measurements)
