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
from cirq_iqm import IQMDevice
from cirq_iqm.iqm_client import CircuitDTO, IQMClient, SingleQubitMappingDTO
from cirq_iqm.iqm_operation_mapping import map_operation


def _serialize_circuit(circuit: cirq.Circuit) -> CircuitDTO:
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


def _serialize_qubit_mapping(qubit_mapping: dict[str, str]):
    """Serializes a qubit mapping dict into the corresponding IQM data transfer format"""
    return [SingleQubitMappingDTO(logical_name=k, physical_name=v) for k, v in qubit_mapping.items()]


class IQMSampler(cirq.work.Sampler):
    """Circuit sampler for executing quantum circuits on IQM quantum computers.

    Args:
        url: Endpoint for accessing the server interface. Has to start with http or https.
        settings: Settings for the quantum computer.
        qubit_mapping: A dict that maps logical qubit names to physical qubit names
    """
    def __init__(self, url: str, settings: str, device: IQMDevice, qubit_mapping: dict[str, str] = None):
        settings_json = json.loads(settings)

        if not qubit_mapping:
            # If qubit_mapping empty or None create identity mapping
            qubit_mapping = {qubit.name: qubit.name for qubit in device.qubits}
        else:
            # verify that the given qubit_mapping is injective
            if not len(set(qubit_mapping.values())) == len(qubit_mapping.values()):
                raise ValueError('Multiple logical qubits map to the same physical qubit')

        # verify that all target qubits in qubit_mapping are defined in the settings
        if not all(qubit in settings_json['subtrees'] for qubit in qubit_mapping.values()):
            raise ValueError('One or more qubits do not have matching definition in the settings')

        self._client = IQMClient(url, settings=settings_json)
        self._device = device
        self._qubit_mapping = qubit_mapping

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

        if program.device is cirq.UNCONSTRAINED_DEVICE:
            # verify that qubit_mapping covers all qubits in the circuit
            circuit_qubits = set(qubit.name for qubit in program.all_qubits())
            if not circuit_qubits.issubset(set(self._qubit_mapping.keys())):
                raise ValueError('Provided qubit_mapping does not cover all qubits in the circuit')
        elif program.device != self._device:
            raise ValueError('The devices of the given circuit and of the sampler are not the same')

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
        iqm_circuit = _serialize_circuit(circuit)
        qubit_mapping = _serialize_qubit_mapping(self._qubit_mapping)

        job_id = self._client.submit_circuit(iqm_circuit, qubit_mapping, repetitions)
        results = self._client.wait_for_results(job_id)
        measurements = {k: np.array(v) for k, v in results.measurements.items()}
        return study.Result(params=resolver.ParamResolver(), measurements=measurements)
