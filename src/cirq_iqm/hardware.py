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
Implements a CIRQ compatible sampler that calls the IQM backend
"""

import datetime
import enum
import json
import os
import random
import string
from typing import Dict, Iterable, List, Optional, Sequence, Set, TypeVar, Union, TYPE_CHECKING

import cirq
from google.protobuf import any_pb2
from cirq.google.engine.client import quantum
from cirq.google.engine.result_type import ResultType
from cirq import circuits, study, value
from cirq.google import serializable_gate_set as sgs
from cirq.google.api import v2
from cirq.google.arg_func_langs import arg_to_proto
from cirq.google.engine import (
    engine_client,
    engine_program,
    engine_job,
    engine_processor,
    engine_sampler,
)
from cirq import study
import numpy as np
from .iqm_client import IQMBackendClient, RunStatus
from iqm_client import IQMCircuit, IQMInstruction


def get_sampler():
    env_token = "IQM_TOKEN"
    env_url = "IQM_URL"
    for env_var in [env_url, env_token]:
        if not os.environ.get(env_var):
            raise EnvironmentError(f'Environment variable {env_var} is not set.')
    return IQMSampler(url=os.environ.get(env_url), token=os.environ.get(env_token))


def serialize_iqm(circuit: cirq.Circuit) -> dict:
    """
    Converts cirq circuit to IQM compatible representation.
    """
    instructions = []
    for moment in circuit.moments:
        for operation in moment.operations:
            gate_dict = operation.gate._json_dict_()
            gate = operation.gate
            instructions.append(
                IQMInstruction(
                    name=gate_dict["cirq_type"],
                    qubits=[qubit.name for qubit in operation.qubits],
                    args={key: val for key, val in gate_dict.items() if key is not "cirq_type"}
                )
            )

    circuit_dict = IQMCircuit(
        name="Serialized from cirq",
        instructions=instructions
    )
    return circuit_dict


class IQMSampler(cirq.work.Sampler):
    def __init__(self, url, token):
        self._client = IQMBackendClient(url, token)

    def run_sweep(
            self,
            program: 'cirq.Circuit',
            params: 'cirq.Sweepable',
            repetitions: int = 1,
    ) -> List['cirq.Result']:
        sweeps = study.to_sweeps(params or study.ParamResolver({}))
        results = []
        results.append(self._send_circuit(program))
        return results

    def _send_circuit(
            self,
            circuit: 'cirq.Circuit',
            repetitions: int = 1
    ) -> cirq.study.Result:
        """Sends the json string to the remote Pasqal device
        Args:
            serialization_str: Json representation of the circuit.
            repetitions: Number of repetitions.
        Returns:
            json representation of the results
        """
        iqm_circuit = serialize_iqm(circuit)
        job_id = self._client.submit_circuit(circuit=iqm_circuit, shots=repetitions)
        results = self._client.wait_results(job_id)
        measurements = {key:np.array(value) for (key,value) in results.measurements.items()}
        return study.Result(params={}, measurements=measurements)
