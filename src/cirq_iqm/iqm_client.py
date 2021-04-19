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
import requests
from enum import Enum
from datetime import datetime

TIMEOUT_SECONDS = 10
SECONDS_BETWEEN_CALLS=1

class IQMException(Exception):
    pass


class ApiTimeoutError(IQMException):
    pass


class RunStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"
    FAILED = "failed"


@dataclass(frozen=True)
class IQMInstruction:
    name: str
    qubits: list[str]
    args: dict


@dataclass(frozen=True)
class IQMCircuit:
    name: str
    args: dict
    instructions: list[IQMInstruction]


@dataclass(frozen=True)
class QubitMapping:
    logical_name: str
    physical_name: str


@dataclass(frozen=True)
class RunResult():
    status: RunStatus

    @staticmethod
    def parse(input: dict):
        if input["status"]==RunStatus.READY:
            return RunReady(**input)
        elif input["status"]==RunStatus.PENDING:
            return RunPending(**input)
        elif input["status"]==RunStatus.FAILED:
            return RunError(**input)
        else:
            raise Exception(f"Unknown message status: {input['status']}")

@dataclass(frozen=True)
class RunPending(RunResult):
    pass

@dataclass(frozen=True)
class RunReady(RunResult):
    measurements: dict[str:list[list]]

@dataclass(frozen=True)
class RunFailed(RunResult):
    message: str


class IQMBackendClient:
    def __init__(self, url: str, token: str):
        self._token = token
        self._base_url = url

    def submit_circuit(self, circuit: IQMCircuit, mappings: list[QubitMapping] = {}, shots: int = 1) -> int:
        """
        Submits circuit to the IQM backend
        Args:
            circuit: Circuit to be executed on the IQM backend
            mappings: Mappings of human-readable names to physical names
            shots: number of repetitions

        Returns:
            ID for the created task. This ID is needed to query the status and the execution results

        """
        result = requests.post(f"{self._base_url}/circuit/run", data={
            "mappings": mappings,
            "circuit": circuit,
            "shots": shots
        })
        result.raise_for_status()
        return json.loads(result.text)["id"]

    def get_run(self, id) -> RunResult:
        """
        Query the status of the running task
        Args:
            id: id of the taks

        Returns:
            Run result (can be Pending)

        Raises:
            HTTPException for http exceptions
            IQMException for IQM backend specific exceptions

        """
        result = requests.get(f"{self._base_url}/circuit/run/{id}")
        result.raise_for_status()
        result=RunResult.parse(json.loads(result.text))
        if result.status == RunStatus.FAILED:
            raise IQMException(parsed_result["message"])
        return result

    def wait_results(self, id, timeout_secs=TIMEOUT_SECONDS) -> RunResult:
        """
        Poll results until run is Ready/Failed or timed out
        Args:
            id: id of the task to wait
            timeout_secs: how long to wait for a response before raising an ApiTimeoutError

        Returns:
            Run result

        Raises:
            ApiTimeoutError if time exceeded the set timeout

        """
        start_time = datetime.now()
        while (datetime.now() - start_time).total_seconds() < timeout_secs:
            results = self.get_run(id)
            if results.status != RunStatus.PENDING:
                return results
            time.sleep(SECONDS_BETWEEN_CALLS)
        raise ApiTimeoutError(f"The task didn't finish in {timeout_secs} seconds")
