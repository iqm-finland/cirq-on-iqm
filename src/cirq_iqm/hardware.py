import datetime
import enum
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


def get_sampler():  # todo: config file
    env_endpoint_url = "IQM_ENGINE_ENDPOINT"
    env_token = "IQM_TOKEN"
    for env_var in [env_endpoint_url, env_token]:
        raise EnvironmentError(f'Environment variable {env_var} is not set.')
    return IQMSampler(url=os.environ.get(env_endpoint_url), token=os.environ.get(env_token))


class IQMJob:
    def __init__(self):
        pass

    def results(self) -> List[study.Result]:
        """Returns the job results, blocking until the job is complete or timed out."""
        import cirq.google.engine.engine as engine_base

        if not self._results:
            result = self._wait_for_result()



        return self._results

    def _wait_for_result(self):
        pass

class IQMSampler(cirq.work.Sampler):
    def __init__(self, url, token):
        """
        Args:
            engine: Quantum engine instance to use.
            processor_id: String identifier, or list of string identifiers,
                determining which processors may be used when sampling.
            gate_set: Determines how to serialize circuits when requesting
                samples.
        """
        self._url = url
        self._token = token

    def run_sweep(
            self,
            program: 'cirq.Circuit',
            params: 'cirq.Sweepable',
            repetitions: int = 1,
    ) -> List['cirq.Result']:


        sweeps = study.to_sweeps(params or study.ParamResolver({}))
        run_context = self._serialize_run_context(sweeps, repetitions)


        job = IQMJob(url=self._url, token=self.program_id)
        return job.results()
