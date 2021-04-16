from dataclasses import dataclass
import json
import requests
from enum import Enum
from datetime import datetime

BASE_URL = "https://meetiqm.com/api/"

class IQMException(Exception):
    pass

class ApiTimeoutError(IQMException):
    pass

class RunStatus(str, Enum):
    PENDING="pending"
    READY="ready"
    FAILED="failed"

class IQMBackendClient:
    def __init__(self, token):
        self._token=token

    def submit_circuit(self, mapping:dict, circuit:dict, shots:int=1) -> int:
        result = requests.post(f"{BASE_URL}/circuit/run", data={
            "mapping": mapping,
            "circuit": circuit,
            "shots": shots
        })
        result.raise_for_status()

        return json.loads(result.text)["id"]

    def get_run_status(self, id) -> dict:
        result = requests.get(f"{BASE_URL}/circuit/run/{id}")
        result.raise_for_status()
        return json.loads(result.text)

    def wait_results(self,id, timeout_secs=10)->dict:
        start_time=datetime.now()
        while (datetime.now()-start_time).total_seconds()<timeout_secs:
            results=self.get_run_status(id)
            if results["status"] != RunStatus.PENDING:
                return results
        raise ApiTimeoutError(f"The task didn't finish in {timeout_secs} seconds")



