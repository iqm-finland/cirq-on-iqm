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
from importlib.metadata import version
import uuid

import cirq
from iqm_client import Circuit, Instruction, IQMClient, Metadata, RunRequest, RunResult, Status
from mockito import ANY, mock, when
import pytest
import sympy  # type: ignore

from cirq_iqm import Adonis
from cirq_iqm.iqm_sampler import IQMSampler


@pytest.fixture()
def circuit():
    qubit_1 = cirq.NamedQubit('QB1')
    qubit_2 = cirq.NamedQubit('QB2')
    return cirq.Circuit(cirq.measure(qubit_1, qubit_2, key='result'))


@pytest.fixture()
def iqm_metadata():
    return Metadata(
        request=RunRequest(
            shots=4,
            circuits=[
                Circuit(
                    name='circuit_1',
                    instructions=(
                        Instruction(name='measurement', implementation=None, qubits=('QB1',), args={'key': 'm1'}),
                    ),
                )
            ],
        )
    )


@pytest.fixture()
def adonis_sampler(base_url):
    return IQMSampler(base_url, Adonis())


@pytest.mark.usefixtures('unstub')
def test_run_sweep_executes_circuit_with_physical_names(adonis_sampler, circuit, iqm_metadata):
    client = mock(IQMClient)
    run_id = uuid.uuid4()
    run_result = RunResult(status=Status.READY, measurements=[{'some stuff': [[0], [1]]}], metadata=iqm_metadata)
    when(client).submit_circuits(ANY, calibration_set_id=ANY, shots=ANY, circuit_duration_check=ANY).thenReturn(run_id)
    when(client).wait_for_results(run_id).thenReturn(run_result)

    adonis_sampler._client = client
    results = adonis_sampler.run_sweep(circuit, None, repetitions=2)
    assert isinstance(results[0], cirq.Result)


@pytest.mark.usefixtures('unstub')
def test_run_sweep_executes_circuit_with_calibration_set_id(base_url, circuit, iqm_metadata):
    client = mock(IQMClient)
    run_id = uuid.uuid4()
    calibration_set_id = uuid.uuid4()
    sampler = IQMSampler(base_url, Adonis(), calibration_set_id=calibration_set_id)
    run_result = RunResult(status=Status.READY, measurements=[{'some stuff': [[0], [1]]}], metadata=iqm_metadata)
    when(client).submit_circuits(
        ANY, calibration_set_id=calibration_set_id, shots=ANY, circuit_duration_check=ANY
    ).thenReturn(run_id)
    when(client).wait_for_results(run_id).thenReturn(run_result)

    sampler._client = client
    results = sampler.run_sweep(circuit, None, repetitions=2)
    assert isinstance(results[0], cirq.Result)


@pytest.mark.usefixtures('unstub')
def test_run_sweep_executes_circuit_with_duration_check_disabled(base_url, circuit, iqm_metadata):
    client = mock(IQMClient)
    run_id = uuid.uuid4()
    sampler = IQMSampler(base_url, Adonis(), circuit_duration_check=False)
    run_result = RunResult(status=Status.READY, measurements=[{'some stuff': [[0], [1]]}], metadata=iqm_metadata)
    when(client).submit_circuits(ANY, calibration_set_id=ANY, shots=ANY, circuit_duration_check=False).thenReturn(
        run_id
    )
    when(client).wait_for_results(run_id).thenReturn(run_result)

    sampler._client = client
    results = sampler.run_sweep(circuit, None, repetitions=2)
    assert isinstance(results[0], cirq.Result)


@pytest.mark.usefixtures('unstub')
def test_run_sweep_with_parameter_sweep(adonis_sampler, iqm_metadata):
    client = mock(IQMClient)
    run_id = uuid.uuid4()
    run_result = RunResult(
        status=Status.READY, measurements=[{'some stuff': [[0]]}, {'some stuff': [[1]]}], metadata=iqm_metadata
    )
    when(client).submit_circuits(ANY, calibration_set_id=ANY, shots=ANY, circuit_duration_check=ANY).thenReturn(run_id)
    when(client).wait_for_results(run_id).thenReturn(run_result)
    qubit_1 = cirq.NamedQubit('QB1')
    qubit_2 = cirq.NamedQubit('QB2')
    circuit_sweep = cirq.Circuit(cirq.X(qubit_1) ** sympy.Symbol('t'), cirq.measure(qubit_1, qubit_2, key='result'))

    sweep_length = 2
    param_sweep = cirq.Linspace('t', start=0, stop=1, length=sweep_length)

    adonis_sampler._client = client

    results = adonis_sampler.run_sweep(circuit_sweep, param_sweep, repetitions=123)
    assert len(results) == sweep_length
    assert all(isinstance(result, cirq.Result) for result in results)


@pytest.mark.usefixtures('unstub')
def test_run_iqm_batch(adonis_sampler, iqm_metadata):
    client = mock(IQMClient)
    run_id = uuid.uuid4()
    run_result = RunResult(
        status=Status.READY, measurements=[{'some stuff': [[0]]}, {'some stuff': [[1]]}], metadata=iqm_metadata
    )
    when(client).submit_circuits(ANY, calibration_set_id=ANY, shots=ANY, circuit_duration_check=ANY).thenReturn(run_id)
    when(client).wait_for_results(run_id).thenReturn(run_result)

    qubit_1 = cirq.NamedQubit('QB1')
    qubit_2 = cirq.NamedQubit('QB2')
    circuit1 = cirq.Circuit(cirq.X(qubit_1), cirq.measure(qubit_1, qubit_2, key='result'))
    circuit2 = cirq.Circuit(cirq.X(qubit_2), cirq.measure(qubit_1, qubit_2, key='result'))
    circuits = [circuit1, circuit2]

    adonis_sampler._client = client
    results = adonis_sampler.run_iqm_batch(circuits, repetitions=123)

    assert len(results) == len(circuits)
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


@pytest.mark.usefixtures('unstub')
def test_client_signature_is_passed_to_client():
    """Test that IQMSampler set client signature"""
    sampler = IQMSampler('http://some-url.iqm.fi', Adonis())
    assert f'cirq-iqm {version("cirq-iqm")}' in sampler._client._signature


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
