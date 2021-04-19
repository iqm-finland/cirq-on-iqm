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
from typing import Iterable, Optional, Sequence, Set, TypeVar, Union, TYPE_CHECKING

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
from cirq_iqm.iqm_client import IQMBackendClient, RunStatus, IQMCircuit, IQMInstruction


def get_sampler_from_env() -> 'IQMSampler':
    """
    Initialize an IQM sampler using environment variables IQM_TOKEN and IQM_URL

    Returns:
        IQM Sampler
    """
    IQM_URL = os.environ.get("IQM_URL")
    IQM_TOKEN = os.environ.get("IQM_TOKEN")
    if not IQM_URL or not IQM_TOKEN:
        raise EnvironmentError(f'Environment variables IQM_URL or IQM_TOKEN are not set.')
    return IQMSampler(url=IQM_URL, token=IQM_TOKEN)


def _serialize_iqm(circuit: cirq.Circuit) -> IQMCircuit:
    """
    Converts cirq circuit to IQM compatible representation.
    Args:
        circuit: Circuit to serialize

    Returns:
        IQM circuit object
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
                    args={key: val for key, val in gate_dict.items() if key != "cirq_type"}
                )
            )

    circuit_dict = IQMCircuit(
        name="Serialized from cirq",
        instructions=instructions,
        args={}  # todo: implement arguments
    )
    return circuit_dict


class IQMSampler(cirq.work.Sampler):
    """
    IQM implementation of a cirq sampler.
    Allows to sample circuits using a real backend
    """

    def __init__(self, url, token):
        self._client = IQMBackendClient(url, token)

    def run_sweep(
            self,
            program: 'cirq.Circuit',
            params: 'cirq.Sweepable',
            repetitions: int = 1,
    ) -> list['cirq.Result']:
        """Samples from the given Circuit.

        In contrast to run, this allows for sweeping over different parameter
        values.

        Args:
            program: The circuit to sample from.
            params: Parameters to run with the program (NOT IMPLEMENTED, leave empty)
            repetitions: The number of times to sample.

        Returns:
            Result list for this run; one for each possible parameter
            resolver.

        Raises:
            NotImplementedError
        """
        sweeps = study.to_sweeps(params or study.ParamResolver({}))
        if len(sweeps) > 1 or len(sweeps[0].keys) > 0:
            raise NotImplementedError("Sweeps are not supported")
        results = [self._send_circuit(program)]
        return results

    def _send_circuit(
            self,
            circuit: 'cirq.Circuit',
            repetitions: int = 1
    ) -> cirq.study.Result:
        """
        Sends the circuit to the remote IQM device
        Args:
            circuit: Circuit to run
            repetitions: Number of repetitions

        Returns:
        Results of the run

        Raises:
            IQMException
            ApiTimeoutError
        """
        iqm_circuit = _serialize_iqm(circuit)
        job_id = self._client.submit_circuit(circuit=iqm_circuit, shots=repetitions)
        results = self._client.wait_results(job_id)
        measurements = {k: np.array(v) for k, v in results.measurements.items()}
        return study.Result(params={}, measurements=measurements)
