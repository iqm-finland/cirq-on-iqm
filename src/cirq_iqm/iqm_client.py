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
Client for calling the IQM backend.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from posixpath import join
from typing import Any, Optional, Union
from uuid import UUID

import requests



TIMEOUT_SECONDS = 10
SECONDS_BETWEEN_CALLS = 1


class CircuitExecutionException(Exception):
    """Something went wrong on the server side.
    """


class APITimeoutError(CircuitExecutionException):
    """Exception for when executing a task on the backend takes too long.
    """


class RunStatus(str, Enum):
    """
    Status of a task
    """
    PENDING = "pending"
    READY = "ready"
    FAILED = "failed"


@dataclass(frozen=True)
class InstructionDTO:
    """DTO for operations constituting a quantum circuit.
    """
    name: str
    qubits: list[str]
    args: dict[str, Any]


@dataclass(frozen=True)
class CircuitDTO:
    """DTO for quantum circuits.
    """
    name: str
    args: dict[str, Any]
    instructions: list[InstructionDTO]


@dataclass(frozen=True)
class SingleQubitMapping:
    """Mapping of a logical qubit to a physical qubit.
    """
    logical_name: str
    physical_name: str


@dataclass(frozen=True)
class RunResult:
    """Results of a circuit execution.

    * ``measurements`` is present iff the status is ``'ready'``.
    * ``message`` carries additional information for the ``'failed'`` status.
    * If the status is ``'pending'``, ``measurements`` and ``message`` are ``None``.
    """
    status: RunStatus
    measurements: Optional[dict[str, list[list[int]]]] = None
    message: Optional[str] = None

    @staticmethod
    def from_dict(inp: dict[str, Union[str, dict]]) -> RunResult:
        """Parses the result from a dict.

        Args:
            inp: value to parse, has to map to RunResult

        Returns:
            parsed RunResult

        """
        input_copy = inp.copy()
        return RunResult(status=RunStatus(input_copy.pop("status")), **input_copy)


class IQMBackendClient:
    """Provides access to a remote IQM quantum device.

    Args:
        url: Endpoint for accessing the device. Has to start with http or https.
    """
    def __init__(self, url: str):
        self._base_url = url

    def submit_circuit(
            self,
            circuit: CircuitDTO,
            qubit_mapping: list[SingleQubitMapping] = None,
            shots: int = 1
    ) -> UUID:
        """Submits a quantum circuit to be executed on the backend.

        Args:
            circuit: circuit to be executed
            qubit_mapping: mapping of human-readable qubit names to physical qubit names
            shots: number of times the circuit is sampled

        Returns:
            ID for the created task. This ID is needed to query the status and the execution results.
        """
        result = requests.post(join(self._base_url, "circuit/run"), data={
            "mapping": qubit_mapping,
            "circuit": circuit,
            "shots": shots
        })
        result.raise_for_status()
        return UUID(json.loads(result.text)["id"])

    def get_run(self, run_id: UUID) -> RunResult:
        """Query the status of the running task.

        Args:
            run_id: id of the taks

        Returns:
            result of the run (can be pending)

        Raises:
            HTTPException: http exceptions
            CircuitExecutionException: IQM backend specific exceptions

        """
        result = requests.get(join(self._base_url, "circuit/run/", str(run_id)))
        result.raise_for_status()
        result = RunResult.from_dict(json.loads(result.text))
        if result.status == RunStatus.FAILED:
            raise CircuitExecutionException(result.message)
        return result

    def wait_for_results(self, run_id: UUID, timeout_secs: float = TIMEOUT_SECONDS) -> RunResult:
        """Poll results until run is ready, failed, or timed out.

        Args:
            run_id: id of the task to wait
            timeout_secs: how long to wait for a response before raising an APITimeoutError

        Returns:
            run result

        Raises:
            APITimeoutError: time exceeded the set timeout

        """
        start_time = datetime.now()
        while (datetime.now() - start_time).total_seconds() < timeout_secs:
            results = self.get_run(run_id)
            if results.status != RunStatus.PENDING:
                return results
            time.sleep(SECONDS_BETWEEN_CALLS)
        raise APITimeoutError(f"The task didn't finish in {timeout_secs} seconds.")
