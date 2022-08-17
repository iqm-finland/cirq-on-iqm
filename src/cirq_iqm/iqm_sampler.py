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

from typing import Any, Optional

import cirq
import numpy as np
from cirq import study
from iqm_client import iqm_client
from iqm_client.iqm_client import IQMClient

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


class IQMSampler(cirq.work.Sampler):
    """Circuit sampler for executing quantum circuits on IQM quantum computers.

    Args:
        url: Endpoint for accessing the server interface. Has to start with http or https.
        device: Quantum architecture to execute the circuits on
        settings: Settings for the quantum computer
        calibration_set_id: ID of the calibration set to use instead of ``settings``

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
            *,
            qubit_mapping: Optional[dict[str, str]] = None,
            settings: Optional[dict[str, Any]] = None,
            calibration_set_id: Optional[int] = None,
            **user_auth_args  # contains keyword args auth_server_url, username and password
    ):
        self._settings = settings
        self._calibration_set_id = calibration_set_id
        self._client = IQMClient(url, **user_auth_args)
        self._device = device
        self._qubit_mapping = qubit_mapping

    def close_client(self):
        """Close IQMClient's session with the user authentication server. Discard the client."""
        if not self._client:
            return
        self._client.close_auth_session()
        self._client = None

    def run_sweep(
            self,
            program: cirq.Circuit,
            params: cirq.Sweepable,
            repetitions: int = 1
    ) -> list[cirq.Result]:
        mapped = program
        if self._qubit_mapping is not None:
            # apply the qubit_mapping
            qubit_map = {cirq.NamedQubit(k): cirq.NamedQubit(v) for k, v in self._qubit_mapping.items()}
            try:
                mapped = program.transform_qubits(qubit_map)
            except ValueError as e:
                raise ValueError('Failed applying qubit mapping.') from e

        # validate the circuit for the device. If qubit_mapping was  given then validation is done after applying it,
        # otherwise it is assumed that the circuit already contains device qubits, and it is validated as is.
        self._device.validate_circuit(mapped)

        resolvers = list(cirq.to_resolvers(params))

        circuits = [
            cirq.protocols.resolve_parameters(program, res) for res in resolvers
        ] if resolvers else [program]

        measurements = self._send_circuits(circuits,
                                           repetitions=repetitions,
                                           qubit_mapping=self._qubit_mapping,
                                           settings=self._settings,
                                           calibration_set_id=self._calibration_set_id)
        return [
            study.ResultDict(params=res, measurements=mes)
            for res, mes in zip(resolvers, measurements)
        ]

    def _send_circuits(  # pylint: disable=too-many-arguments
            self,
            circuits: list[cirq.Circuit],
            qubit_mapping: Optional[dict[str, str]],
            settings: Optional[dict[str, Any]],
            calibration_set_id: Optional[int],
            repetitions: int = 1
    ) -> list[dict[str, np.ndarray]]:
        """Sends the circuit(s) to be executed.

        Args:
            circuits: quantum circuit(s) to execute
            qubit_mapping: Mapping of qubit names.
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

        job_id = self._client.submit_circuits(
            serialized_circuits,
            qubit_mapping=qubit_mapping,
            settings=settings,
            calibration_set_id=calibration_set_id,
            shots=repetitions
        )
        results = self._client.wait_for_results(job_id)
        if results.measurements is None:
            raise RuntimeError('No measurements returned from IQM quantum computer.')

        return [
            {k: np.array(v) for k, v in measurements.items()}
            for measurements in results.measurements
        ]
