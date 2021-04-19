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

from dataclasses import dataclass
import json
import requests
from enum import Enum
from datetime import datetime

TIMEOUT_SECONDS=10

class IQMException(Exception):
    pass

class ApiTimeoutError(IQMException):
    pass

class RunStatus(str, Enum):
    PENDING="pending"
    READY="ready"
    FAILED="failed"

class IQMBackendClient:
    def __init__(self, url:str, token:str):
        self._token=token
        self._base_url=url

    def submit_circuit(self, circuit:dict, mappings:list[dict[str,str]]={}, shots:int=1) -> int:
        result = requests.post(f"{self._base_url}/circuit/run", data={
            "mappings": mappings,
            "circuit": circuit,
            "shots": shots
        })
        result.raise_for_status()
        return json.loads(result.text)["id"]

    def get_run_status(self, id) -> dict:
        result = requests.get(f"{self._base_url}/circuit/run/{id}")
        result.raise_for_status()
        return json.loads(result.text)

    def wait_results(self,id, timeout_secs=TIMEOUT_SECONDS)->dict:
        start_time=datetime.now()
        while (datetime.now()-start_time).total_seconds()<timeout_secs:
            results=self.get_run_status(id)
            if results["status"] != RunStatus.PENDING:
                return results
        raise ApiTimeoutError(f"The task didn't finish in {timeout_secs} seconds")



