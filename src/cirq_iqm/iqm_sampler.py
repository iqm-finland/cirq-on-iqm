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
Circuit sampler that executes quantum circuits on an IQM quantum computer.
"""
from __future__ import annotations

import json
from typing import Optional

import cirq
import numpy as np
from cirq import study
from iqm_client import iqm_client
from iqm_client.iqm_client import IQMClient, SingleQubitMapping

from cirq_iqm import IQMDevice
from cirq_iqm.iqm_operation_mapping import map_operation


def serialize_circuit(circuit: cirq.Circuit) -> iqm_client.Circuit:
    """Serializes a quantum circuit into the IQM data transfer format.

    Args:
        circuit: quantum circuit to serialize

    Returns:
        data transfer object representing the circuit
    """
    instructions = list(map(map_operation, circuit.all_operations()))
    return iqm_client.Circuit(
        name='Serialized from Cirq',
        instructions=instructions
    )


def serialize_qubit_mapping(qubit_mapping: dict[str, str]) -> list[SingleQubitMapping]:
    """Serializes a qubit mapping dict into the corresponding IQM data transfer format.

    Args:
        qubit_mapping: mapping from logical to physical qubit names

    Returns:
        data transfer object representing the mapping
    """
    return [SingleQubitMapping(logical_name=k, physical_name=v) for k, v in qubit_mapping.items()]


class IQMSampler(cirq.work.Sampler):
    """Circuit sampler for executing quantum circuits on IQM quantum computers.

    Args:
        url: Endpoint for accessing the server interface. Has to start with http or https.
        device: Quantum architecture to execute the circuits on
        settings: Settings for the quantum computer
        qubit_mapping: Injective dictionary that maps logical qubit names to physical qubit names

    Keyword Args:
        auth_server_url: URL of user authentication server, if required by the IQM Cortex server.
            This can also be set in the IQM_AUTH_SERVER environment variable.
        username: Username, if required by the IQM Cortex server.
            This can also be set in the IQM_AUTH_USERNAME environment variable.
        password: Password, if required by the IQM Cortex server.
            This can also be set in the IQM_AUTH_PASSWORD environment variable.
    """
    def __init__(
            self,
            url: str,
            device: IQMDevice,
            settings: Optional[str] = None,
            qubit_mapping: Optional[dict[str, str]] = None,
            **user_auth_args  # contains keyword args auth_server_url, username and password
    ):
        settings_json = None if not settings else json.loads(settings)

        if qubit_mapping is None:
            # If qubit_mapping is not given, create an identity mapping
            qubit_mapping = {qubit.name: qubit.name for qubit in device.qubits}
        else:
            # verify that the given qubit_mapping is injective
            if not len(set(qubit_mapping.values())) == len(qubit_mapping.values()):
                raise ValueError('Multiple logical qubits map to the same physical qubit.')

            # verify that all the physical qubit names in qubit_mapping are defined in the settings
            target_qubits = set(qubit_mapping.values())
            if settings_json is not None:
                physical_qubits = set(settings_json['subtrees'])  # pylint: disable=unsubscriptable-object
                diff = target_qubits - physical_qubits
            else:
                diff = set()  # with settings set to None qubit names can not be checked
            if diff:
                raise ValueError(f'The physical qubits {diff} in the qubit mapping are not defined in the settings.')

        self._client = IQMClient(url, settings_json, **user_auth_args)
        self._device = device
        self._qubit_mapping = qubit_mapping

    def close_client(self):
        """Close IQMClient's session with the user authentication server. Discard the client."""
        if not self._client:
            return
        self._client.close()
        self._client = None

    def run_sweep(
            self,
            program: cirq.Circuit,
            params: cirq.Sweepable,
            repetitions: int = 1,
    ) -> list[cirq.Result]:
        # verify that qubit_mapping covers all qubits in the circuit
        circuit_qubits = set(qubit.name for qubit in program.all_qubits())
        diff = circuit_qubits - set(self._qubit_mapping)
        if diff:
            raise ValueError(f'The qubits {diff} are not found in the provided qubit mapping.')

        # apply qubit_mapping
        qubit_map = {cirq.NamedQubit(k): cirq.NamedQubit(v) for k, v in self._qubit_mapping.items()}
        mapped = program.transform_qubits(qubit_map)

        # validate the circuit for the device
        # check that the circuit connectivity fits in the device connectivity
        self._device.validate_circuit(mapped)

        resolvers = list(cirq.to_resolvers(params))

        circuits = [
            cirq.protocols.resolve_parameters(program, res) for res in resolvers
        ] if resolvers else [program]

        measurements = self._send_circuits(circuits, repetitions=repetitions)
        return [
            study.ResultDict(params=res, measurements=mes)
            for res, mes in zip(resolvers, measurements)
        ]

    def _send_circuits(
            self,
            circuits: list[cirq.Circuit],
            repetitions: int = 1,
    ) -> list[dict[str, np.ndarray]]:
        """Sends the circuit(s) to be executed.

        Args:
            circuits: quantum circuit(s) to execute
            repetitions: number of times the circuit(s) are sampled

        Returns:
            results of the execution

        Raises:
            CircuitExecutionError: something went wrong on the server
            APITimeoutError: server did not return the results in the allocated time
            RuntimeError: IQM client session has been closed
        """
        if not self._client:
            raise RuntimeError(
                'Cannot submit circuits since session to IQM client has been closed.'
            )
        serialized_circuits = [serialize_circuit(circuit) for circuit in circuits]
        qubit_mapping = serialize_qubit_mapping(self._qubit_mapping)

        job_id = self._client.submit_circuits(serialized_circuits, qubit_mapping, repetitions)
        results = self._client.wait_for_results(job_id)
        if results.measurements is None:
            raise RuntimeError('No measurements returned from IQM quantum computer.')

        return [
            {k: np.array(v) for k, v in measurements.items()}
            for measurements in results.measurements
        ]
