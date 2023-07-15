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

from dataclasses import dataclass
from importlib.metadata import version
from typing import List, Mapping, Optional
import sys
from uuid import UUID
import warnings

import cirq
import iqm_client
from iqm_client import HeraldingMode, IQMClient, RunRequest, JobAbortionError
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
        run_sweep_timeout:
            timeout to poll sweep results in seconds.
        circuit_duration_check: whether to enable or disable server-side circuit duration check
        heralding_mode: Heralding mode to use during execution.

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
        run_sweep_timeout: Optional[int] = None,
        circuit_duration_check: bool = True,
        heralding_mode: HeraldingMode = HeraldingMode.NONE,
        **user_auth_args,  # contains keyword args auth_server_url, username and password
    ):
        self._client = IQMClient(url, client_signature=f'cirq-iqm {version("cirq-iqm")}', **user_auth_args)
        if device is None:
            device_metadata = IQMDeviceMetadata.from_architecture(self._client.get_quantum_architecture())
            self._device = IQMDevice(device_metadata)
        else:
            self._device = device
        self._calibration_set_id = calibration_set_id
        self._run_sweep_timeout = run_sweep_timeout
        self._circuit_duration_check = circuit_duration_check
        self._heralding_mode = heralding_mode

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
    ) -> list[IQMResult]:

        # validate the circuit for the device
        self._device.validate_circuit(program)

        resolvers = list(cirq.to_resolvers(params))

        circuits = [cirq.protocols.resolve_parameters(program, res) for res in resolvers] if resolvers else [program]

        circuit_results = self._send_circuits(
            circuits,
            repetitions=repetitions,
        )
        results = [
            IQMResult(
                params=res,
                measurements=result.measurements,
                records=result.records,
                metadata=result.metadata,
            )
            for res, result in zip(resolvers, circuit_results)
        ]

        return results

    def run_iqm_batch(self, programs: list[cirq.Circuit], repetitions: int = 1) -> list[IQMResult]:
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

        circuit_results = self._send_circuits(
            programs,
            repetitions=repetitions,
        )
        results = [
            IQMResult(
                params=cirq.ParamResolver(),
                measurements=result.measurements,
                records=result.records,
                metadata=result.metadata,
            )
            for result in circuit_results
        ]

        return results

    def _send_circuits(
        self,
        circuits: list[cirq.Circuit],
        repetitions: int = 1,
    ) -> List[IQMResult]:
        """Sends a batch of circuits to be executed and retrieves the results.

        If a user interrupts the program while it is waiting for results, attempts to abort the submitted job.
        """

        if not self._client:
            raise RuntimeError('Cannot submit circuits since session to IQM client has been closed.')
        serialized_circuits = [serialize_circuit(circuit) for circuit in circuits]

        job_id = self._client.submit_circuits(
            serialized_circuits,
            calibration_set_id=self._calibration_set_id,
            shots=repetitions,
            circuit_duration_check=self._circuit_duration_check,
            heralding_mode=self._heralding_mode,
        )
        try:
            timeout_arg = [self._run_sweep_timeout] if self._run_sweep_timeout is not None else []
            results = self._client.wait_for_results(job_id, *timeout_arg)
            if results.measurements is None:
                raise RuntimeError('No measurements returned from IQM quantum computer.')

            return [
                self._create_iqm_result(
                    result_dict=cirq.ResultDict(
                        params=None, measurements={k: np.array(v) for k, v in measurements.items()}
                    ),
                    job_id=job_id,
                    calibration_set_id=results.metadata.calibration_set_id,
                    request=results.metadata.request,
                )
                for measurements in results.measurements
            ]

        except KeyboardInterrupt:
            try:
                self._client.abort_job(job_id)
            except JobAbortionError as e:
                warnings.warn(f'Failed to abort job: {e}')
            finally:
                sys.exit()

    def _create_iqm_result(
        self,
        result_dict: cirq.ResultDict,
        job_id: UUID,
        calibration_set_id: Optional[UUID],
        request: RunRequest,
    ) -> IQMResult:
        # pylint: disable=no-self-use
        """
        Creates an IQMResult instance with the given attributes.
        """
        return IQMResult(
            params=result_dict.params,
            measurements=result_dict.measurements,
            metadata=ResultMetadata(
                job_id=job_id,
                calibration_set_id=calibration_set_id,
                request=request,
            ),
        )


@dataclass
class ResultMetadata:
    """Metadata for an IQM execution result.

    Attributes:
        job_id: A UUID representing the job.
        calibration_set_id: A UUID representing the calibration set used for this result.
        request: A RunRequest object representing the request made to run the circuit.
    """

    job_id: UUID
    calibration_set_id: Optional[UUID]
    request: RunRequest


class IQMResult(cirq.ResultDict):
    """A class to store the result of a quantum circuit execution on an IQM device.

    Args:
        params: A cirq.ParamResolver of settings used for this result
        measurements: A dictionary of measurement keys to measurement results. This is a 2-D array of booleans.
        records: A dictionary of meaurement keys to measurement results. This is a 3D array of booleans.
        metadata: Metadata for results from IQM circuit execution.
    """

    def __init__(
        self,
        *,
        params: Optional[cirq.ParamResolver] = None,
        measurements: Optional[Mapping[str, np.ndarray]] = None,
        records: Optional[Mapping[str, np.ndarray]] = None,
        metadata=ResultMetadata,
    ) -> None:
        super().__init__(params=params, measurements=measurements, records=records)
        self.metadata = metadata
