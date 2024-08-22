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
import sys
import uuid

import cirq
from mockito import ANY, expect, mock, verify, verifyNoUnwantedInteractions, when
import numpy as np
import pytest
import sympy  # type: ignore

from iqm.cirq_iqm import Adonis
import iqm.cirq_iqm as module_under_test
from iqm.cirq_iqm.iqm_sampler import IQMResult, IQMSampler, ResultMetadata, serialize_circuit
from iqm.iqm_client import (
    Circuit,
    HeraldingMode,
    Instruction,
    IQMClient,
    JobAbortionError,
    Metadata,
    RunRequest,
    RunResult,
    Status,
)


@pytest.fixture()
def circuit_physical():
    """Circuit with physical qubit names"""
    qubit_1 = cirq.NamedQubit('QB1')
    qubit_2 = cirq.NamedQubit('QB2')
    return cirq.Circuit(cirq.measure(qubit_1, qubit_2, key='result'))


@pytest.fixture()
def circuit_non_physical():
    """Circuit with non-physical qubit names"""
    qubit_1 = cirq.NamedQubit('Alice')
    qubit_2 = cirq.NamedQubit('Bob')
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


@pytest.fixture
def create_run_request_default_kwargs() -> dict:
    return {
        'calibration_set_id': None,
        'shots': 1,
        'max_circuit_duration_over_t2': None,
        'heralding_mode': HeraldingMode.NONE,
    }


@pytest.fixture
def job_id():
    return uuid.uuid4()


@pytest.fixture
def run_request():
    run_request = mock(RunRequest)
    return run_request


@pytest.mark.usefixtures('unstub')
def test_run_sweep_raises_with_non_physical_names(adonis_sampler, circuit_non_physical):
    with pytest.raises(ValueError, match='Qubit not on device'):
        adonis_sampler.run_sweep(circuit_non_physical, None)


@pytest.mark.usefixtures('unstub')
def test_run_sweep_executes_circuit_with_physical_names(
    adonis_sampler, circuit_physical, iqm_metadata, create_run_request_default_kwargs, job_id, run_request
):
    # pylint: disable=too-many-arguments
    client = mock(IQMClient)
    run_result = RunResult(status=Status.READY, measurements=[{'some stuff': [[0], [1]]}], metadata=iqm_metadata)
    when(client).create_run_request(ANY, **create_run_request_default_kwargs).thenReturn(run_request)
    when(client).submit_run_request(run_request).thenReturn(job_id)
    when(client).wait_for_results(job_id).thenReturn(run_result)

    adonis_sampler._client = client
    results = adonis_sampler.run_sweep(circuit_physical, None)
    assert isinstance(results[0], IQMResult)
    assert isinstance(results[0].metadata, ResultMetadata)
    np.testing.assert_array_equal(results[0].measurements['some stuff'], np.array([[0], [1]]))


@pytest.mark.usefixtures('unstub')
def test_run_sweep_executes_circuit_with_calibration_set_id(
    base_url, circuit_physical, iqm_metadata, create_run_request_default_kwargs, job_id, run_request
):
    # pylint: disable=too-many-arguments
    client = mock(IQMClient)
    calibration_set_id = uuid.uuid4()
    sampler = IQMSampler(base_url, Adonis(), calibration_set_id=calibration_set_id)
    run_result = RunResult(status=Status.READY, measurements=[{'some stuff': [[0], [1]]}], metadata=iqm_metadata)
    kwargs = create_run_request_default_kwargs | {'calibration_set_id': calibration_set_id}
    when(client).create_run_request(ANY, **kwargs).thenReturn(run_request)
    when(client).submit_run_request(run_request).thenReturn(job_id)
    when(client).wait_for_results(job_id).thenReturn(run_result)

    sampler._client = client
    results = sampler.run_sweep(circuit_physical, None)
    assert isinstance(results[0], IQMResult)
    assert isinstance(results[0].metadata, ResultMetadata)
    np.testing.assert_array_equal(results[0].measurements['some stuff'], np.array([[0], [1]]))


@pytest.mark.usefixtures('unstub')
def test_run_sweep_has_duration_check_enabled_by_default(
    base_url, circuit_physical, iqm_metadata, create_run_request_default_kwargs, job_id, run_request
):
    # pylint: disable=too-many-arguments
    client = mock(IQMClient)
    sampler = IQMSampler(base_url, Adonis())
    run_result = RunResult(status=Status.READY, measurements=[{'some stuff': [[0], [1]]}], metadata=iqm_metadata)
    kwargs = create_run_request_default_kwargs | {'max_circuit_duration_over_t2': None}
    when(client).create_run_request(ANY, **kwargs).thenReturn(run_request)
    when(client).submit_run_request(run_request).thenReturn(job_id)
    when(client).wait_for_results(job_id).thenReturn(run_result)

    sampler._client = client
    results = sampler.run_sweep(circuit_physical, None)
    assert isinstance(results[0], IQMResult)
    assert isinstance(results[0].metadata, ResultMetadata)
    np.testing.assert_array_equal(results[0].measurements['some stuff'], np.array([[0], [1]]))


@pytest.mark.usefixtures('unstub')
def test_run_sweep_executes_circuit_with_duration_check_disabled(
    base_url, circuit_physical, iqm_metadata, create_run_request_default_kwargs, job_id, run_request
):
    # pylint: disable=too-many-arguments
    client = mock(IQMClient)
    sampler = IQMSampler(base_url, Adonis(), max_circuit_duration_over_t2=0.0)
    run_result = RunResult(status=Status.READY, measurements=[{'some stuff': [[0], [1]]}], metadata=iqm_metadata)
    kwargs = create_run_request_default_kwargs | {'max_circuit_duration_over_t2': 0.0}
    when(client).create_run_request(ANY, **kwargs).thenReturn(run_request)
    when(client).submit_run_request(run_request).thenReturn(job_id)
    when(client).wait_for_results(job_id).thenReturn(run_result)

    sampler._client = client
    results = sampler.run_sweep(circuit_physical, None)
    assert isinstance(results[0], IQMResult)
    assert isinstance(results[0].metadata, ResultMetadata)
    np.testing.assert_array_equal(results[0].measurements['some stuff'], np.array([[0], [1]]))


@pytest.mark.usefixtures('unstub')
def test_run_sweep_allows_to_override_polling_timeout(
    base_url, circuit_physical, create_run_request_default_kwargs, iqm_metadata, job_id, run_request
):
    # pylint: disable=too-many-arguments
    client = mock(IQMClient)
    timeout = 123
    sampler = IQMSampler(base_url, Adonis(), run_sweep_timeout=timeout)
    run_result = RunResult(status=Status.READY, measurements=[{'some stuff': [[0], [1]]}], metadata=iqm_metadata)
    when(client).create_run_request(ANY, **create_run_request_default_kwargs).thenReturn(run_request)
    when(client).submit_run_request(run_request).thenReturn(job_id)
    when(client).wait_for_results(job_id, timeout).thenReturn(run_result)

    sampler._client = client
    results = sampler.run_sweep(circuit_physical, None)
    assert isinstance(results[0], IQMResult)
    assert isinstance(results[0].metadata, ResultMetadata)
    np.testing.assert_array_equal(results[0].measurements['some stuff'], np.array([[0], [1]]))


@pytest.mark.usefixtures('unstub')
def test_run_sweep_has_heralding_mode_none_by_default(
    base_url, circuit_physical, iqm_metadata, create_run_request_default_kwargs, job_id, run_request
):
    # pylint: disable=too-many-arguments
    client = mock(IQMClient)
    sampler = IQMSampler(base_url, Adonis())
    run_result = RunResult(status=Status.READY, measurements=[{'some stuff': [[0], [1]]}], metadata=iqm_metadata)
    kwargs = create_run_request_default_kwargs | {'heralding_mode': HeraldingMode.NONE}
    when(client).create_run_request(ANY, **kwargs).thenReturn(run_request)
    when(client).submit_run_request(run_request).thenReturn(job_id)
    when(client).wait_for_results(job_id).thenReturn(run_result)

    sampler._client = client
    results = sampler.run_sweep(circuit_physical, None)
    assert isinstance(results[0], IQMResult)
    assert isinstance(results[0].metadata, ResultMetadata)
    np.testing.assert_array_equal(results[0].measurements['some stuff'], np.array([[0], [1]]))


@pytest.mark.usefixtures('unstub')
def test_run_sweep_executes_circuit_with_heralding_mode_zeros(
    base_url, circuit_physical, iqm_metadata, create_run_request_default_kwargs, job_id, run_request
):
    # pylint: disable=too-many-arguments
    client = mock(IQMClient)
    sampler = IQMSampler(base_url, Adonis(), heralding_mode=HeraldingMode.ZEROS)
    run_result = RunResult(status=Status.READY, measurements=[{'some stuff': [[0], [1]]}], metadata=iqm_metadata)
    kwargs = create_run_request_default_kwargs | {'heralding_mode': HeraldingMode.ZEROS}
    when(client).create_run_request(ANY, **kwargs).thenReturn(run_request)
    when(client).submit_run_request(run_request).thenReturn(job_id)
    when(client).wait_for_results(job_id).thenReturn(run_result)

    sampler._client = client
    results = sampler.run_sweep(circuit_physical, None)
    assert isinstance(results[0], IQMResult)
    assert isinstance(results[0].metadata, ResultMetadata)
    np.testing.assert_array_equal(results[0].measurements['some stuff'], np.array([[0], [1]]))


@pytest.mark.usefixtures('unstub')
def test_run_sweep_with_parameter_sweep(
    adonis_sampler, iqm_metadata, create_run_request_default_kwargs, job_id, run_request
):
    client = mock(IQMClient)
    run_result = RunResult(
        status=Status.READY, measurements=[{'some stuff': [[0]]}, {'some stuff': [[1]]}], metadata=iqm_metadata
    )
    when(client).create_run_request(ANY, **create_run_request_default_kwargs).thenReturn(run_request)
    when(client).submit_run_request(run_request).thenReturn(job_id)
    when(client).wait_for_results(job_id).thenReturn(run_result)
    qubit_1 = cirq.NamedQubit('QB1')
    qubit_2 = cirq.NamedQubit('QB2')
    circuit_sweep = cirq.Circuit(cirq.X(qubit_1) ** sympy.Symbol('t'), cirq.measure(qubit_1, qubit_2, key='result'))

    sweep_length = 2
    param_sweep = cirq.Linspace('t', start=0, stop=1, length=sweep_length)

    adonis_sampler._client = client

    results = adonis_sampler.run_sweep(circuit_sweep, param_sweep)
    assert len(results) == sweep_length
    assert all(isinstance(result, IQMResult) for result in results)
    assert all(isinstance(result.metadata, ResultMetadata) for result in results)
    np.testing.assert_array_equal(results[0].measurements['some stuff'], np.array([[0]]))
    np.testing.assert_array_equal(results[1].measurements['some stuff'], np.array([[1]]))
    for idx, param in enumerate(param_sweep):
        assert results[idx].params == param


@pytest.mark.usefixtures('unstub')
def test_run_sweep_abort_job_successful(
    adonis_sampler, circuit_physical, create_run_request_default_kwargs, job_id, recwarn, run_request
):
    # pylint: disable=too-many-arguments
    client = mock(IQMClient)
    when(client).create_run_request(ANY, **create_run_request_default_kwargs).thenReturn(run_request)
    when(client).submit_run_request(run_request).thenReturn(job_id)
    when(client).wait_for_results(job_id).thenRaise(KeyboardInterrupt)
    when(client).abort_job(job_id)
    when(sys).exit().thenRaise(NotImplementedError)  # just for testing without actually exiting python

    adonis_sampler._client = client
    with pytest.raises(NotImplementedError):
        adonis_sampler.run_sweep(circuit_physical, None)

    assert len(recwarn) == 0
    verify(client, times=1).abort_job(job_id)
    verify(sys, times=1).exit()


@pytest.mark.usefixtures('unstub')
def test_run_sweep_abort_job_failed(
    adonis_sampler, circuit_physical, create_run_request_default_kwargs, job_id, run_request
):
    client = mock(IQMClient)
    when(client).create_run_request(ANY, **create_run_request_default_kwargs).thenReturn(run_request)
    when(client).submit_run_request(run_request).thenReturn(job_id)
    when(client).wait_for_results(job_id).thenRaise(KeyboardInterrupt)
    when(client).abort_job(job_id).thenRaise(JobAbortionError)
    when(sys).exit().thenRaise(NotImplementedError)  # just for testing without actually exiting python

    adonis_sampler._client = client
    with pytest.warns(UserWarning, match='Failed to abort job'):
        with pytest.raises(NotImplementedError):
            adonis_sampler.run_sweep(circuit_physical, None)

    verify(client, times=1).abort_job(job_id)
    verify(sys, times=1).exit()


@pytest.mark.usefixtures('unstub')
def test_run_iqm_batch_raises_with_non_physical_names(adonis_sampler, circuit_non_physical):
    with pytest.raises(ValueError, match='Qubit not on device'):
        adonis_sampler.run_iqm_batch([circuit_non_physical])


@pytest.mark.usefixtures('unstub')
def test_run_iqm_batch(adonis_sampler, iqm_metadata, create_run_request_default_kwargs, job_id, run_request):
    client = mock(IQMClient)
    repetitions = 123
    run_result = RunResult(
        status=Status.READY, measurements=[{'some stuff': [[0]]}, {'some stuff': [[1]]}], metadata=iqm_metadata
    )
    kwargs = create_run_request_default_kwargs | {'shots': repetitions}
    when(client).create_run_request(ANY, **kwargs).thenReturn(run_request)
    when(client).submit_run_request(run_request).thenReturn(job_id)
    when(client).wait_for_results(job_id).thenReturn(run_result)

    qubit_1 = cirq.NamedQubit('QB1')
    qubit_2 = cirq.NamedQubit('QB2')
    circuit1 = cirq.Circuit(cirq.X(qubit_1), cirq.measure(qubit_1, qubit_2, key='result'))
    circuit2 = cirq.Circuit(cirq.X(qubit_2), cirq.measure(qubit_1, qubit_2, key='result'))
    circuits = [circuit1, circuit2]

    adonis_sampler._client = client
    results = adonis_sampler.run_iqm_batch(circuits, repetitions=repetitions)

    assert len(results) == len(circuits)
    assert all(isinstance(result, IQMResult) for result in results)
    assert all(isinstance(result.metadata, ResultMetadata) for result in results)
    np.testing.assert_array_equal(results[0].measurements['some stuff'], np.array([[0]]))
    np.testing.assert_array_equal(results[1].measurements['some stuff'], np.array([[1]]))


@pytest.mark.usefixtures('unstub')
def test_run_iqm_batch_allows_to_override_polling_timeout(
    base_url, iqm_metadata, create_run_request_default_kwargs, job_id, run_request
):
    client = mock(IQMClient)
    run_result = RunResult(
        status=Status.READY, measurements=[{'some stuff': [[0]]}, {'some stuff': [[1]]}], metadata=iqm_metadata
    )
    timeout = 123
    sampler = IQMSampler(base_url, Adonis(), run_sweep_timeout=timeout)
    when(client).create_run_request(ANY, **create_run_request_default_kwargs).thenReturn(run_request)
    when(client).submit_run_request(run_request).thenReturn(job_id)
    when(client).wait_for_results(job_id, timeout).thenReturn(run_result)

    qubit_1 = cirq.NamedQubit('QB1')
    qubit_2 = cirq.NamedQubit('QB2')
    circuit1 = cirq.Circuit(cirq.X(qubit_1), cirq.measure(qubit_1, qubit_2, key='result'))
    circuit2 = cirq.Circuit(cirq.X(qubit_2), cirq.measure(qubit_1, qubit_2, key='result'))
    circuits = [circuit1, circuit2]

    sampler._client = client
    results = sampler.run_iqm_batch(circuits)

    assert len(results) == len(circuits)
    assert all(isinstance(result, IQMResult) for result in results)
    np.testing.assert_array_equal(results[0].measurements['some stuff'], np.array([[0]]))
    np.testing.assert_array_equal(results[1].measurements['some stuff'], np.array([[1]]))


@pytest.mark.usefixtures('unstub')
def test_credentials_are_passed_to_client():
    user_auth_args = {
        'auth_server_url': 'https://fake.auth.server.com',
        'username': 'fake-username',
        'password': 'fake-password',
    }
    when(module_under_test.iqm_sampler).IQMClient('http://url', client_signature=ANY, **user_auth_args).thenReturn(
        mock(IQMClient)
    )
    IQMSampler('http://url', Adonis(), **user_auth_args)
    verify(module_under_test.iqm_sampler, times=1).IQMClient('http://url', client_signature=ANY, **user_auth_args)


@pytest.mark.usefixtures('unstub')
def test_client_signature_is_passed_to_client():
    """Test that IQMSampler set client signature"""
    sampler = IQMSampler('http://some-url.iqm.fi', Adonis())
    assert f'cirq-iqm {version("cirq-iqm")}' in sampler._client._signature


@pytest.mark.usefixtures('unstub')
def test_close_client():
    user_auth_args = {
        'auth_server_url': 'https://fake.auth.server.com',
        'username': 'fake-username',
        'password': 'fake-password',
    }
    sampler = IQMSampler('http://url', Adonis(), **user_auth_args)
    mock_client = mock(IQMClient)
    sampler._client = mock_client
    when(mock_client).close_auth_session().thenReturn(True)
    sampler.close_client()
    verify(mock_client, times=1).close_auth_session()


@pytest.mark.usefixtures('unstub')
def test_create_run_request_for_run(
    adonis_sampler, iqm_metadata, job_id, create_run_request_default_kwargs, run_request
):
    client = mock(IQMClient)
    adonis_sampler._client = client
    repetitions = 123
    kwargs = create_run_request_default_kwargs | {'shots': repetitions}
    run_result = RunResult(status=Status.READY, measurements=[{'some stuff': [[0], [1]]}], metadata=iqm_metadata)

    qubit_1 = cirq.NamedQubit('QB1')
    qubit_2 = cirq.NamedQubit('QB2')
    circuit = cirq.Circuit(cirq.X(qubit_1), cirq.measure(qubit_1, qubit_2, key='result'))

    # verifies that sampler.create_run_request() and sampler.run() call client.create_run_request() with same arguments
    expect(client, times=2).create_run_request(
        [serialize_circuit(circuit)],
        **kwargs,
    ).thenReturn(run_request)
    when(client).submit_run_request(run_request).thenReturn(job_id)
    when(client).wait_for_results(job_id).thenReturn(run_result)

    assert adonis_sampler.create_run_request(circuit, repetitions=repetitions) == run_request
    adonis_sampler.run(circuit, repetitions=repetitions)

    verifyNoUnwantedInteractions()


@pytest.mark.usefixtures('unstub')
def test_create_run_request_for_run_iqm_batch(
    adonis_sampler, iqm_metadata, job_id, create_run_request_default_kwargs, run_request
):
    # pylint: disable=too-many-locals
    client = mock(IQMClient)
    adonis_sampler._client = client
    repetitions = 123
    kwargs = create_run_request_default_kwargs | {'shots': repetitions}
    run_result = RunResult(
        status=Status.READY, measurements=[{'some stuff': [[0]]}, {'some stuff': [[1]]}], metadata=iqm_metadata
    )

    qubit_1 = cirq.NamedQubit('QB1')
    qubit_2 = cirq.NamedQubit('QB2')
    circuit1 = cirq.Circuit(cirq.X(qubit_1), cirq.measure(qubit_1, qubit_2, key='result'))
    circuit2 = cirq.Circuit(cirq.X(qubit_2), cirq.measure(qubit_1, qubit_2, key='result'))
    circuits = [circuit1, circuit2]

    # verifies that sampler.create_run_request() and sampler.run_iqm_batch() call client.create_run_request() with
    # same arguments
    expect(client, times=2).create_run_request(
        [serialize_circuit(c) for c in circuits],
        **kwargs,
    ).thenReturn(run_request)
    when(client).submit_run_request(run_request).thenReturn(job_id)
    when(client).wait_for_results(job_id).thenReturn(run_result)

    assert adonis_sampler.create_run_request(circuits, repetitions=repetitions) == run_request
    adonis_sampler.run_iqm_batch(circuits, repetitions=repetitions)

    verifyNoUnwantedInteractions()
