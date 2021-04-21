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
Implements a client for calling the IQM backend
"""
import time
from dataclasses import dataclass
import json
from enum import Enum
from datetime import datetime
from typing import Any, Union
from posixpath import join
import requests
TIMEOUT_SECONDS = 10
SECONDS_BETWEEN_CALLS = 1


class CircuitExecutionException(Exception):
    """
    Something went wrong on the server side
    """


class ApiTimeoutError(CircuitExecutionException):
    """
    Exception for when executing a task on the backend takes too long
    """


class RunStatus(str, Enum):
    """
    Status of a task
    """
    PENDING = "pending"
    READY = "ready"
    FAILED = "failed"


@dataclass(frozen=True)
class IQMInstruction:
    """
    Transfer DTO for IQM insrtructions
    """
    name: str
    qubits: list[str]
    args: dict[str, Any]


@dataclass(frozen=True)
class IQMCircuit:
    """
    Transfer DTO for IQM circuit
    """
    name: str
    args: dict
    instructions: list[IQMInstruction]


@dataclass(frozen=True)
class QubitMapping:
    """
    Mapping of logical qubits to physical qubits
    """
    logical_name: str
    physical_name: str


@dataclass(frozen=True)
class RunResult:
    """
    Result of a task execution.
    Measurements present only if the status is "ready".
    Message carries the additional information for the "failed" status.
    Measurements and messages expected to be None if the status is "pending"
    """
    status: RunStatus
    measurements: dict[str:list[list]] = None
    message: str = None

    @staticmethod
    def from_dict(inp: dict[str, Union[str, dict]]):
        """
        Parses the result from a dict
        Args:
            inp: value to parse, has to map to Run result

        Returns:
            Parsed object of RunResult

        """
        input_copy = inp.copy()
        return RunResult(status=RunStatus(input_copy.pop("status")), **input_copy)


class IQMBackendClient:
    """
    Class to access backend quantum computer
    """

    def __init__(self, url: str):
        """
        Init
        Args:
            url: Endpoint for accessing the quantum computer. Has to start with http or https.
        """
        self._base_url = url

    def submit_circuit(self, circuit: IQMCircuit, mappings: list[QubitMapping] = None, shots: int = 1) -> int:
        """
        Submits circuit to the IQM backend
        Args:
            circuit: Circuit to be executed on the IQM backend
            mappings: Mappings of human-readable names to physical names
            shots: number of repetitions

        Returns:
            ID for the created task. This ID is needed to query the status and the execution results

        """
        result = requests.post(join(self._base_url, "circuit/run"), data={
            "mappings": mappings,
            "circuit": circuit,
            "shots": shots
        })
        result.raise_for_status()
        return json.loads(result.text)["id"]

    def get_run(self, run_id: int) -> RunResult:
        """
        Query the status of the running task
        Args:
            run_id: id of the taks

        Returns:
            Run result (can be Pending)

        Raises:
            HTTPException for http exceptions
            CircuitExecutionException for IQM backend specific exceptions

        """
        result = requests.get(join(self._base_url, "circuit/run/", str(run_id)))
        result.raise_for_status()
        result = RunResult.from_dict(json.loads(result.text))
        if result.status == RunStatus.FAILED:
            raise CircuitExecutionException(result.message)
        return result

    def wait_for_results(self, run_id: int, timeout_secs: float = TIMEOUT_SECONDS) -> RunResult:
        """
        Poll results until run is Ready/Failed or timed out
        Args:
            run_id: id of the task to wait
            timeout_secs: how long to wait for a response before raising an ApiTimeoutError

        Returns:
            Run result

        Raises:
            ApiTimeoutError if time exceeded the set timeout

        """
        start_time = datetime.now()
        while (datetime.now() - start_time).total_seconds() < timeout_secs:
            results = self.get_run(run_id)
            if results.status != RunStatus.PENDING:
                return results
            time.sleep(SECONDS_BETWEEN_CALLS)
        raise ApiTimeoutError(f"The task didn't finish in {timeout_secs} seconds")
