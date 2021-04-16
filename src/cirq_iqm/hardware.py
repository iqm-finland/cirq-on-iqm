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
from .iqm_client import IQMBackendClient

def get_sampler():
    env_token = "IQM_TOKEN"
    if not os.environ.get(env_token):
        raise EnvironmentError(f'Environment variable {env_var} is not set.')
    return IQMSampler(token=os.environ.get(env_token))


def serialize_iqm(circuit: cirq.Circuit)-> dict:
    """
    Converts cirq circuit to IQM compatible representation.
    """
    instructions=[]
    for moment in circuit.moments:
        for operation in moment.operations:
            gate_dict=operation.gate._json_dict_()
            gate=operation.gate
            instructions.append({
                "name":gate_dict["cirq_type"],
                "qubits":[qubit.name for qubit in operation.qubits],
                "args": {key:val for key,val in gate_dict.items() if key is not "cirq_type"}
            })


    circuit_dict = {
        "name": "",
        "instructions": instructions
    }
    return circuit_dict

class IQMSampler(cirq.work.Sampler):
    def __init__(self, token):
        """
        Args:
        """
        self._token = token

    def run_sweep(
            self,
            program: 'cirq.Circuit',
            params: 'cirq.Sweepable',
            repetitions: int = 1,
    ) -> List['cirq.Result']:


        sweeps = study.to_sweeps(params or study.ParamResolver({}))
        result=self._send_circuit(program)

        return result

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
        client=IQMBackendClient(self._token)
        iqm_circuit = serialize_iqm(circuit) # todo: get device here?
        job_id=client.submit_circuit(mapping={},circuit=iqm_circuit,shots=repetitions) # todo: mapping?
        results=client.wait_results(job_id)
        # todo: check if failed

        result_serialized = self._retrieve_serialized_result(task_id)
        result = cirq.read_json(json_text=result_serialized)

        return result

