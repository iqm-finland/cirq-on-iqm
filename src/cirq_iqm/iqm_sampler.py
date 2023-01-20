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

from typing import Optional
from uuid import UUID

import cirq
from cirq import study
from iqm_client import iqm_client
from iqm_client.iqm_client import IQMClient
import numpy as np

from cirq_iqm.devices.iqm_device import IQMDevice, IQMDeviceMetadata
from cirq_iqm.iqm_operation_mapping import map_operation


def serialize_circuit(circuit: cirq.Circuit) -> iqm_client.Circuit:
    """Serializes a quantum circuit into the IQM data transfer format.

    Args:
        circuit: quantum circuit to serialize

    Returns:
        data transfer object representing the circuit
    """
    instructions = list(map(map_operation, circuit.all_operations()))
    return iqm_client.Circuit(name='Serialized from Cirq', instructions=instructions)


class IQMSampler(cirq.work.Sampler):
    """Circuit sampler for executing quantum circuits on IQM quantum computers.

    Args:
        url: Endpoint for accessing the server interface. Has to start with http or https.
        device: Device to execute the circuits on. If ``None``, the device will be created based
            on the quantum architecture obtained from :class:`.IQMClient`.
        calibration_set_id:
            ID of the calibration set to use. If ``None``, use the latest one.

    Keyword Args:
        auth_server_url (str): URL of user authentication server, if required by the IQM Cortex server.
            This can also be set in the IQM_AUTH_SERVER environment variable.
        username (str): Username, if required by the IQM Cortex server.
            This can also be set in the IQM_AUTH_USERNAME environment variable.
        password (str): Password, if required by the IQM Cortex server.
            This can also be set in the IQM_AUTH_PASSWORD environment variable.
    """

    def __init__(
        self,
        url: str,
        device: Optional[IQMDevice] = None,
        *,
        calibration_set_id: Optional[UUID] = None,
        **user_auth_args,  # contains keyword args auth_server_url, username and password
    ):
        self._client = IQMClient(url, **user_auth_args)
        if device is None:
            device_metadata = IQMDeviceMetadata.from_architecture(self._client.get_quantum_architecture())
            self._device = IQMDevice(device_metadata)
        else:
            self._device = device
        self._calibration_set_id = calibration_set_id

    @property
    def device(self) -> IQMDevice:
        """Returns the device used by the sampler."""
        return self._device

    def close_client(self):
        """Close IQMClient's session with the user authentication server. Discard the client."""
        if not self._client:
            return
        self._client.close_auth_session()
        self._client = None

    def run_sweep(  # type: ignore[override]
        self, program: cirq.Circuit, params: cirq.Sweepable, repetitions: int = 1
    ) -> list[cirq.Result]:

        # validate the circuit for the device
        self._device.validate_circuit(program)

        resolvers = list(cirq.to_resolvers(params))

        circuits = [cirq.protocols.resolve_parameters(program, res) for res in resolvers] if resolvers else [program]

        measurements = self._send_circuits(
            circuits,
            calibration_set_id=self._calibration_set_id,
            repetitions=repetitions,
        )
        return [study.ResultDict(params=res, measurements=mes) for res, mes in zip(resolvers, measurements)]

    def run_iqm_batch(self, programs: list[cirq.Circuit], repetitions: int = 1) -> list[cirq.Result]:
        """Sends a batch of circuits to be executed.

        Running circuits in a batch is more efficient and hence completes quicker than running the circuits
        individually. Circuits run in a batch must all measure the same qubits.

        Args:
            programs: quantum circuits to execute
            repetitions: number of times the circuits are sampled

        Returns:
            results of the execution

        Raises:
            ValueError: circuits are not valid for execution
            CircuitExecutionError: something went wrong on the server
            APITimeoutError: server did not return the results in the allocated time
            RuntimeError: IQM client session has been closed
        """
        # validate each circuit for the device
        for program in programs:
            self._device.validate_circuit(program)

        measurements = self._send_circuits(
            programs,
            calibration_set_id=self._calibration_set_id,
            repetitions=repetitions,
        )

        return [study.ResultDict(measurements=meas) for meas in measurements]

    def _send_circuits(
        self,
        circuits: list[cirq.Circuit],
        calibration_set_id: Optional[UUID],
        repetitions: int = 1,
    ) -> list[dict[str, np.ndarray]]:
        """Sends a batch of circuits to be executed."""

        if not self._client:
            raise RuntimeError('Cannot submit circuits since session to IQM client has been closed.')
        serialized_circuits = [serialize_circuit(circuit) for circuit in circuits]

        job_id = self._client.submit_circuits(
            serialized_circuits, calibration_set_id=calibration_set_id, shots=repetitions
        )
        results = self._client.wait_for_results(job_id)
        if results.measurements is None:
            raise RuntimeError('No measurements returned from IQM quantum computer.')

        return [{k: np.array(v) for k, v in measurements.items()} for measurements in results.measurements]
