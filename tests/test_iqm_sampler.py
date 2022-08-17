# Copyright 2020–2022 Cirq on IQM developers
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
import uuid

import cirq
import pytest
import sympy
from iqm_client.iqm_client import (Circuit, IQMClient, Metadata, RunResult,
                                   Status)
from mockito import ANY, mock, when

from cirq_iqm import Adonis
from cirq_iqm.iqm_sampler import IQMSampler


@pytest.fixture()
def circuit():
    qubit_1 = cirq.NamedQubit('q1 log.')
    qubit_2 = cirq.NamedQubit('q2 log.')
    return cirq.Circuit(
        cirq.measure(qubit_1, qubit_2, key='result')
    )


@pytest.fixture()
def circuit_with_physical_names():
    qubit_1 = cirq.NamedQubit('QB1')
    qubit_2 = cirq.NamedQubit('QB2')
    return cirq.Circuit(
        cirq.measure(qubit_1, qubit_2, key='result')
    )


@pytest.fixture()
def iqm_metadata():
    return Metadata(shots=4, circuits=[Circuit(name='circuit_1', instructions=[])])


@pytest.fixture()
def qubit_mapping():
    return {
        'q1 log.': 'QB1',
        'q2 log.': 'QB2'
    }


@pytest.fixture()
def adonis_sampler(base_url, qubit_mapping):
    return IQMSampler(base_url, Adonis(), qubit_mapping=qubit_mapping)


@pytest.fixture()
def adonis_sampler_without_settings(base_url):
    return IQMSampler(base_url, Adonis())


@pytest.mark.usefixtures('unstub')
def test_run_sweep_executes_circuit(adonis_sampler, circuit, iqm_metadata):
    client = mock(IQMClient)
    run_id = uuid.uuid4()
    run_result = RunResult(status=Status.READY, measurements=[{'some stuff': [[0], [1]]}], metadata=iqm_metadata)
    when(client).submit_circuits(ANY,
                                 qubit_mapping=ANY,
                                 settings=ANY,
                                 calibration_set_id=ANY,
                                 shots=ANY).thenReturn(run_id)
    when(client).wait_for_results(run_id).thenReturn(run_result)

    adonis_sampler._client = client
    results = adonis_sampler.run_sweep(circuit, None, repetitions=2)
    assert isinstance(results[0], cirq.Result)


@pytest.mark.usefixtures('unstub')
def test_run_sweep_with_bad_qubit_mapping(base_url, circuit):
    qubit_mapping = {
        'q1 log.': 'QB1',
        'q2 log.': 'QB1'
    }
    sampler = IQMSampler(base_url, Adonis(), qubit_mapping=qubit_mapping)
    with pytest.raises(ValueError, match='Failed applying qubit mapping.'):
        sampler.run_sweep(circuit, None, repetitions=2)


@pytest.mark.usefixtures('unstub')
def test_run_sweep_executes_circuit_without_settings(adonis_sampler_without_settings,
                                                     circuit_with_physical_names,
                                                     iqm_metadata):
    client = mock(IQMClient)
    run_id = uuid.uuid4()
    run_result = RunResult(status=Status.READY, measurements=[{'some stuff': [[0], [1]]}], metadata=iqm_metadata)
    when(client).submit_circuits(ANY,
                                 qubit_mapping=ANY,
                                 settings=None,
                                 calibration_set_id=ANY,
                                 shots=ANY).thenReturn(run_id)
    when(client).wait_for_results(run_id).thenReturn(run_result)

    adonis_sampler_without_settings._client = client
    results = adonis_sampler_without_settings.run_sweep(circuit_with_physical_names, None, repetitions=2)
    assert isinstance(results[0], cirq.Result)


@pytest.mark.usefixtures('unstub')
def test_run_sweep_with_parameter_sweep(adonis_sampler_without_settings, iqm_metadata):
    client = mock(IQMClient)
    run_id = uuid.uuid4()
    run_result = RunResult(
        status=Status.READY, measurements=[{'some stuff': [[0]]}, {'some stuff': [[1]]}], metadata=iqm_metadata)
    when(client).submit_circuits(ANY,
                                 qubit_mapping=ANY,
                                 settings=ANY,
                                 calibration_set_id=ANY,
                                 shots=ANY).thenReturn(run_id)
    when(client).wait_for_results(run_id).thenReturn(run_result)
    qubit_1 = cirq.NamedQubit('QB1')
    qubit_2 = cirq.NamedQubit('QB2')
    circuit_sweep = cirq.Circuit(cirq.X(qubit_1) ** sympy.Symbol('t'), cirq.measure(qubit_1, qubit_2, key='result'))

    sweep_length = 2
    param_sweep = cirq.Linspace('t', start=0, stop=1, length=sweep_length)

    adonis_sampler_without_settings._client = client

    results = adonis_sampler_without_settings.run_sweep(circuit_sweep, param_sweep, repetitions=123)
    assert len(results) == sweep_length
    assert all(isinstance(result, cirq.Result) for result in results)


def test_credentials_are_passed_to_client():
    user_auth_args = {
        'auth_server_url': 'https://fake.auth.server.com',
        'username': 'fake-username',
        'password': 'fake-password',
    }
    with when(IQMClient)._update_tokens():
        sampler = IQMSampler('http://url', Adonis(), **user_auth_args)
    assert sampler._client._credentials.auth_server_url == user_auth_args['auth_server_url']
    assert sampler._client._credentials.username == user_auth_args['username']
    assert sampler._client._credentials.password == user_auth_args['password']


def test_close_client():
    user_auth_args = {
        'auth_server_url': 'https://fake.auth.server.com',
        'username': 'fake-username',
        'password': 'fake-password',
    }
    with when(IQMClient)._update_tokens():
        sampler = IQMSampler('http://url', Adonis(), **user_auth_args)
    try:
        sampler.close_client()
    except Exception as exc:  # pylint: disable=broad-except
        assert False, f'sampler created with credentials raised an exception {exc} on .close_client()'
