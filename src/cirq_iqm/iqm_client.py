from dataclasses import dataclass
import json
import requests
from enum import Enum
from datetime import datetime

BASE_URL = "https://meetiqm.com/api/"

class IQMException(Exception):
    pass

class APISubmissionError(IQMException):
    pass

class ApiTimeoutError(IQMException):
    pass

class ApiServerError(IQMException):
    pass


class RunStatus(str, Enum):
    RUNNING="running"
    SUCCESS="success"
    FAILURE="failure"

class IQMBackendClient:
    def __init__(self, token):
        self._token=token

    def submit_circuit(self,circuit_definition, mapping, operations, repetitions:int=1) -> int:
        result = requests.post(f"{BASE_URL}/circuit/run", data={
            "circuit_definition": circuit_definition,
            "mapping": mapping,
            "operations": "",
            "repetitions": repetitions
        })
        if result.status_code is not 201:
            raise RunSubmissionError(f"{result.status_code}: {result.reason}")

        return json.loads(result.text)["run_id"]

    def get_run_status(self, id) -> dict:
        result = requests.get(f"{BASE_URL}/circuit/run/{id}")
        if result.status_code is not 200:
            raise ApiServerError(result.reason)

        return json.loads(result.text)

    def wait_results(self,id, timeout_secs=10)->dict:
        start_time=datetime.now()
        while (datetime.now()-start_time).total_seconds()<timeout_secs:
            results=self.get_run_status(id)
            if results["status"] != RunStatus.RUNNING:
                return results
        raise ApiTimeoutError(f"The task didn't finish in {timeout_secs} seconds")



