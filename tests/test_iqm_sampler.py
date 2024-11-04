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
import re
import sys
import uuid
import warnings

import cirq
from mockito import ANY, expect, mock, verify, verifyNoUnwantedInteractions, when
import numpy as np
import pytest
import sympy  # type: ignore

from iqm.cirq_iqm import Adonis, IQMDevice, IQMDeviceMetadata
import iqm.cirq_iqm as module_under_test
from iqm.cirq_iqm.iqm_gates import IQMMoveGate
from iqm.cirq_iqm.iqm_sampler import IQMResult, IQMSampler, ResultMetadata, serialize_circuit
from iqm.iqm_client import (
    Circuit,
    CircuitCompilationOptions,
    CircuitValidationError,
    DynamicQuantumArchitecture,
    GateImplementationInfo,
    GateInfo,
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
def circuit_physical(adonis_architecture):
    """Circuit with physical qubit names"""
    qubit_1 = cirq.NamedQubit('QB1')
    qubit_2 = cirq.NamedQubit('QB2')
    circuit = cirq.Circuit(cirq.measure(qubit_1, qubit_2, key='result'))
    circuit.iqm_calibration_set_id = adonis_architecture.calibration_set_id
    return circuit


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
                        Instruction(name='measure', implementation=None, qubits=('QB1',), args={'key': 'm1'}),
                    ),
                )
            ],
        )
    )


@pytest.fixture()
def adonis_sampler(base_url, adonis_architecture):
    when(IQMClient).get_dynamic_quantum_architecture(None).thenReturn(adonis_architecture)
    return IQMSampler(base_url, device=Adonis())


@pytest.fixture()
def adonis_architecture():
    return DynamicQuantumArchitecture(
        calibration_set_id=uuid.UUID('26c5e70f-bea0-43af-bd37-6212ec7d04cb'),
        qubits=['QB1', 'QB2', 'QB3', 'QB4', 'QB5'],
        computational_resonators=[],
        gates={
            'prx': GateInfo(
                implementations={
                    'drag_gaussian': GateImplementationInfo(loci=(('QB1',), ('QB2',), ('QB3',), ('QB4',), ('QB5',))),
                },
                default_implementation='drag_gaussian',
                override_default_implementation={},
            ),
            'cz': GateInfo(
                implementations={
                    'tgss': GateImplementationInfo(
                        loci=(('QB1', 'QB3'), ('QB2', 'QB3'), ('QB4', 'QB3'), ('QB5', 'QB3'))
                    ),
                },
                default_implementation='tgss',
                override_default_implementation={},
            ),
            'measure': GateInfo(
                implementations={
                    'constant': GateImplementationInfo(loci=(('QB1',), ('QB2',), ('QB3',), ('QB4',), ('QB5',))),
                },
                default_implementation='constant',
                override_default_implementation={},
            ),
        },
    )


@pytest.fixture()
def adonis_sampler_from_architecture(base_url, adonis_architecture):
    when(IQMClient).get_dynamic_quantum_architecture(None).thenReturn(adonis_architecture)
    return IQMSampler(base_url, device=IQMDevice(IQMDeviceMetadata.from_architecture(adonis_architecture)))


@pytest.fixture
def create_run_request_default_kwargs(adonis_architecture) -> dict:
    return {
        'calibration_set_id': adonis_architecture.calibration_set_id,
        'shots': 1,
        'options': CircuitCompilationOptions(),
    }


@pytest.fixture
def job_id():
    return uuid.uuid4()


@pytest.fixture
def run_request():
    run_request = mock(RunRequest)
    return run_request


@pytest.mark.usefixtures('unstub')
def test_init_default(base_url, adonis_architecture):
    when(IQMClient).get_dynamic_quantum_architecture(None).thenReturn(adonis_architecture)
    sampler = IQMSampler(base_url)
    assert sampler.device == IQMDevice(IQMDeviceMetadata.from_architecture(adonis_architecture))
    assert sampler._calibration_set_id == adonis_architecture.calibration_set_id


@pytest.mark.usefixtures('unstub')
def test_init_with_calset_id(base_url, adonis_architecture):
    calset_id = adonis_architecture.calibration_set_id
    when(IQMClient).get_dynamic_quantum_architecture(calset_id).thenReturn(adonis_architecture)
    sampler = IQMSampler(base_url, calibration_set_id=calset_id)
    assert sampler.device == IQMDevice(IQMDeviceMetadata.from_architecture(adonis_architecture))
    assert sampler._calibration_set_id == calset_id


@pytest.mark.usefixtures('unstub')
def test_init_with_calset_id_and_device(base_url, adonis_architecture):
    calset_id = adonis_architecture.calibration_set_id
    when(IQMClient).get_dynamic_quantum_architecture(calset_id).thenReturn(adonis_architecture)
    sampler = IQMSampler(base_url, device=Adonis(), calibration_set_id=calset_id)
    assert sampler.device.metadata == IQMDeviceMetadata.from_architecture(adonis_architecture)
    assert sampler._calibration_set_id == calset_id


@pytest.mark.usefixtures('unstub')
def test_init_warns_if_device_not_compatible_with_default_calset(base_url, fake_arch_with_resonator):
    when(IQMClient).get_dynamic_quantum_architecture(None).thenReturn(fake_arch_with_resonator)
    with pytest.raises(
        ValueError,
        match="'device' is not compatible with the server default calibration set "
        f'{fake_arch_with_resonator.calibration_set_id}',
    ):
        IQMSampler(base_url, device=Adonis())


@pytest.mark.usefixtures('unstub')
def test_init_warns_if_device_not_compatible_with_calset_id(base_url, fake_arch_with_resonator):
    calset_id = uuid.uuid4()
    when(IQMClient).get_dynamic_quantum_architecture(calset_id).thenReturn(fake_arch_with_resonator)
    with pytest.raises(ValueError, match=f"'device' is not compatible with calibration set {calset_id}"):
        IQMSampler(base_url, device=Adonis(), calibration_set_id=calset_id)


@pytest.mark.usefixtures('unstub')
def test_run_sweep_raises_with_non_physical_names(adonis_sampler_from_architecture, circuit_non_physical):
    sampler = adonis_sampler_from_architecture
    when(sampler._client).get_dynamic_quantum_architecture(ANY).thenReturn(sampler.device.metadata.architecture)
    # Note that validation is done in iqm_client, so this is now an integration test.
    with pytest.raises(CircuitValidationError, match="Alice is not allowed as locus for 'measure'"):
        sampler.run_sweep(circuit_non_physical, None)


@pytest.mark.usefixtures('unstub')
def test_run_sweep_executes_circuit_with_physical_names(
    adonis_sampler,
    adonis_architecture,
    circuit_physical,
    iqm_metadata,
    create_run_request_default_kwargs,
    job_id,
    run_request,
):
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    client = mock(IQMClient)
    when(client).get_dynamic_quantum_architecture(None).thenReturn(adonis_architecture)
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
    base_url,
    adonis_architecture,
    circuit_physical,
    iqm_metadata,
    create_run_request_default_kwargs,
    job_id,
    run_request,
):
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    client = mock(IQMClient)
    calibration_set_id = adonis_architecture.calibration_set_id
    when(IQMClient).get_dynamic_quantum_architecture(calibration_set_id).thenReturn(adonis_architecture)
    sampler = IQMSampler(base_url, calibration_set_id=calibration_set_id)
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
    base_url,
    adonis_architecture,
    circuit_physical,
    iqm_metadata,
    create_run_request_default_kwargs,
    job_id,
    run_request,
):
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    client = mock(IQMClient)
    when(IQMClient).get_dynamic_quantum_architecture(None).thenReturn(adonis_architecture)
    sampler = IQMSampler(base_url, device=Adonis())
    run_result = RunResult(status=Status.READY, measurements=[{'some stuff': [[0], [1]]}], metadata=iqm_metadata)
    assert sampler._compiler_options.max_circuit_duration_over_t2 is None
    kwargs = create_run_request_default_kwargs | {
        'options': CircuitCompilationOptions(max_circuit_duration_over_t2=None)
    }
    when(client).get_dynamic_quantum_architecture(None).thenReturn(adonis_architecture)
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
    base_url,
    adonis_architecture,
    circuit_physical,
    iqm_metadata,
    create_run_request_default_kwargs,
    job_id,
    run_request,
):
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    client = mock(IQMClient)
    when(IQMClient).get_dynamic_quantum_architecture(None).thenReturn(adonis_architecture)
    sampler = IQMSampler(
        base_url, device=Adonis(), compiler_options=CircuitCompilationOptions(max_circuit_duration_over_t2=0.0)
    )
    run_result = RunResult(status=Status.READY, measurements=[{'some stuff': [[0], [1]]}], metadata=iqm_metadata)
    assert sampler._compiler_options.max_circuit_duration_over_t2 == 0.0
    kwargs = create_run_request_default_kwargs | {
        'options': CircuitCompilationOptions(max_circuit_duration_over_t2=0.0)
    }
    when(client).get_dynamic_quantum_architecture(None).thenReturn(adonis_architecture)
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
    base_url,
    adonis_architecture,
    circuit_physical,
    create_run_request_default_kwargs,
    iqm_metadata,
    job_id,
    run_request,
):
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    client = mock(IQMClient)
    timeout = 123
    when(IQMClient).get_dynamic_quantum_architecture(None).thenReturn(adonis_architecture)
    sampler = IQMSampler(base_url, device=Adonis(), run_sweep_timeout=timeout)
    run_result = RunResult(status=Status.READY, measurements=[{'some stuff': [[0], [1]]}], metadata=iqm_metadata)
    when(client).get_dynamic_quantum_architecture(None).thenReturn(adonis_architecture)
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
    base_url,
    adonis_architecture,
    circuit_physical,
    iqm_metadata,
    create_run_request_default_kwargs,
    job_id,
    run_request,
):
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    client = mock(IQMClient)
    when(IQMClient).get_dynamic_quantum_architecture(None).thenReturn(adonis_architecture)
    sampler = IQMSampler(base_url, device=Adonis())
    run_result = RunResult(status=Status.READY, measurements=[{'some stuff': [[0], [1]]}], metadata=iqm_metadata)
    kwargs = create_run_request_default_kwargs
    assert sampler._compiler_options.heralding_mode == HeraldingMode.NONE
    when(client).get_dynamic_quantum_architecture(None).thenReturn(adonis_architecture)
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
    base_url,
    adonis_architecture,
    circuit_physical,
    iqm_metadata,
    create_run_request_default_kwargs,
    job_id,
    run_request,
):
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    client = mock(IQMClient)
    when(IQMClient).get_dynamic_quantum_architecture(None).thenReturn(adonis_architecture)
    sampler = IQMSampler(
        base_url, device=Adonis(), compiler_options=CircuitCompilationOptions(heralding_mode=HeraldingMode.ZEROS)
    )
    run_result = RunResult(status=Status.READY, measurements=[{'some stuff': [[0], [1]]}], metadata=iqm_metadata)
    kwargs = create_run_request_default_kwargs | {
        'options': CircuitCompilationOptions(heralding_mode=HeraldingMode.ZEROS)
    }
    assert sampler._compiler_options.heralding_mode == HeraldingMode.ZEROS
    when(client).get_dynamic_quantum_architecture(None).thenReturn(adonis_architecture)
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
    adonis_sampler, adonis_architecture, iqm_metadata, create_run_request_default_kwargs, job_id, run_request
):
    # pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals
    client = mock(IQMClient)
    run_result = RunResult(
        status=Status.READY, measurements=[{'some stuff': [[0]]}, {'some stuff': [[1]]}], metadata=iqm_metadata
    )
    when(client).get_dynamic_quantum_architecture(None).thenReturn(adonis_architecture)
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
    adonis_sampler,
    adonis_architecture,
    circuit_physical,
    create_run_request_default_kwargs,
    job_id,
    recwarn,
    run_request,
):
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    client = mock(IQMClient)
    when(client).get_dynamic_quantum_architecture(None).thenReturn(adonis_architecture)
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
    adonis_sampler, adonis_architecture, circuit_physical, create_run_request_default_kwargs, job_id, run_request
):
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    client = mock(IQMClient)
    when(client).get_dynamic_quantum_architecture(None).thenReturn(adonis_architecture)
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
def test_run_iqm_batch_raises_with_non_physical_names(adonis_sampler_from_architecture, circuit_non_physical):
    sampler = adonis_sampler_from_architecture
    when(sampler._client).get_dynamic_quantum_architecture(ANY).thenReturn(sampler.device.metadata.architecture)
    # Note that validation is done in iqm_client, so this is now an integration test.
    with pytest.raises(CircuitValidationError, match="Alice is not allowed as locus for 'measure'"):
        sampler.run_iqm_batch([circuit_non_physical])

    verifyNoUnwantedInteractions()


@pytest.mark.usefixtures('unstub')
def test_run(adonis_sampler, adonis_architecture, iqm_metadata, create_run_request_default_kwargs, job_id):
    client = mock(IQMClient)
    repetitions = 123
    run_result = RunResult(
        status=Status.READY, measurements=[{'some stuff': [[0]]}, {'some stuff': [[1]]}], metadata=iqm_metadata
    )
    kwargs = create_run_request_default_kwargs | {'shots': repetitions}
    when(client).get_dynamic_quantum_architecture(None).thenReturn(adonis_architecture)
    when(client).create_run_request(ANY, **kwargs).thenReturn(run_request)
    when(client).submit_run_request(run_request).thenReturn(job_id)
    when(client).wait_for_results(job_id).thenReturn(run_result)

    qubit_1 = cirq.NamedQubit('QB1')
    qubit_2 = cirq.NamedQubit('QB2')
    circuit1 = cirq.Circuit(cirq.X(qubit_1), cirq.measure(qubit_1, qubit_2, key='result'))

    adonis_sampler._client = client
    result = adonis_sampler.run(circuit1, repetitions=repetitions)

    assert isinstance(result, IQMResult)
    assert isinstance(result.metadata, ResultMetadata)
    np.testing.assert_array_equal(result.measurements['some stuff'], np.array([[0]]))


@pytest.mark.usefixtures('unstub')
def test_run_ndonis(
    device_with_resonator, fake_arch_with_resonator, base_url, iqm_metadata, create_run_request_default_kwargs, job_id
):
    # pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals
    when(IQMClient).get_dynamic_quantum_architecture(None).thenReturn(fake_arch_with_resonator)
    sampler = IQMSampler(base_url, device=device_with_resonator)
    client = mock(IQMClient)
    when(client).get_dynamic_quantum_architecture(None).thenReturn(fake_arch_with_resonator)
    repetitions = 123
    run_result = RunResult(
        status=Status.READY, measurements=[{'some stuff': [[0]]}, {'some stuff': [[1]]}], metadata=iqm_metadata
    )
    kwargs = create_run_request_default_kwargs | {
        'shots': repetitions,
        'calibration_set_id': device_with_resonator.metadata.architecture.calibration_set_id,
    }
    when(client).create_run_request(ANY, **kwargs).thenReturn(run_request)
    when(client).submit_run_request(run_request).thenReturn(job_id)
    when(client).wait_for_results(job_id).thenReturn(run_result)

    qubit_1, qubit_2 = device_with_resonator.qubits[:2]
    resonator = device_with_resonator.resonators[0]
    circuit = cirq.Circuit()
    circuit.append(device_with_resonator.decompose_operation(cirq.H(qubit_1)))
    circuit.append(IQMMoveGate().on(qubit_1, resonator))
    circuit.append(device_with_resonator.decompose_operation(cirq.H(qubit_2)))
    circuit.append(cirq.CZ(resonator, qubit_2))
    circuit.append(IQMMoveGate().on(qubit_1, resonator))
    circuit.append(device_with_resonator.decompose_operation(cirq.H(qubit_2)))
    circuit.append(cirq.MeasurementGate(2, key='result').on(qubit_1, qubit_2))

    sampler._client = client
    result = sampler.run(circuit, repetitions=repetitions)

    assert isinstance(result, IQMResult)
    assert isinstance(result.metadata, ResultMetadata)
    np.testing.assert_array_equal(result.measurements['some stuff'], np.array([[0]]))


@pytest.mark.usefixtures('unstub')
def test_run_does_not_warn(
    base_url,
    adonis_architecture,
    circuit_physical,
    iqm_metadata,
    create_run_request_default_kwargs,
    job_id,
    run_request,
):  # pylint: disable=too-many-arguments,too-many-positional-arguments
    when(IQMClient).get_dynamic_quantum_architecture(None).thenReturn(adonis_architecture)
    kwargs = create_run_request_default_kwargs | {'calibration_set_id': adonis_architecture.calibration_set_id}
    when(IQMClient).create_run_request(ANY, **kwargs).thenReturn(run_request)
    when(IQMClient).submit_run_request(run_request).thenReturn(job_id)
    when(IQMClient).wait_for_results(job_id).thenReturn(
        RunResult(status=Status.READY, measurements=[{'some stuff': [[0], [1]]}], metadata=iqm_metadata)
    )

    sampler = IQMSampler(base_url)
    routed_circuit, _, _ = sampler.device.route_circuit(circuit_physical)

    with warnings.catch_warnings():
        warnings.simplefilter('error')
        sampler.run(routed_circuit)


@pytest.mark.usefixtures('unstub')
def test_run_warns_if_default_calset_changed(
    base_url,
    adonis_architecture,
    circuit_physical,
    iqm_metadata,
    create_run_request_default_kwargs,
    job_id,
    run_request,
):  # pylint: disable=too-many-arguments,too-many-positional-arguments
    new_default_architecture = DynamicQuantumArchitecture(
        calibration_set_id=uuid.uuid4(),
        qubits=adonis_architecture.qubits,
        computational_resonators=adonis_architecture.computational_resonators,
        gates=adonis_architecture.gates,
    )
    when(IQMClient).get_dynamic_quantum_architecture(None).thenReturn(adonis_architecture).thenReturn(
        new_default_architecture
    )
    kwargs = create_run_request_default_kwargs | {'calibration_set_id': adonis_architecture.calibration_set_id}
    when(IQMClient).create_run_request(ANY, **kwargs).thenReturn(run_request)
    when(IQMClient).submit_run_request(run_request).thenReturn(job_id)
    when(IQMClient).wait_for_results(job_id).thenReturn(
        RunResult(status=Status.READY, measurements=[{'some stuff': [[0], [1]]}], metadata=iqm_metadata)
    )

    sampler = IQMSampler(base_url)
    routed_circuit, _, _ = sampler.device.route_circuit(circuit_physical)

    with pytest.warns(
        UserWarning,
        match=f'default calibration set has changed '
        f'from {adonis_architecture.calibration_set_id} to {new_default_architecture.calibration_set_id}',
    ):
        sampler.run(routed_circuit)


@pytest.mark.usefixtures('unstub')
def test_run_warns_if_circuits_routed_with_different_calset_id(
    base_url,
    adonis_architecture,
    circuit_physical,
    iqm_metadata,
    create_run_request_default_kwargs,
    job_id,
    run_request,
):  # pylint: disable=too-many-arguments,too-many-positional-arguments
    other_calset_id = uuid.uuid4()
    other_architecture = DynamicQuantumArchitecture(
        calibration_set_id=other_calset_id,
        qubits=adonis_architecture.qubits,
        computational_resonators=adonis_architecture.computational_resonators,
        gates=adonis_architecture.gates,
    )
    when(IQMClient).get_dynamic_quantum_architecture(None).thenReturn(adonis_architecture)
    when(IQMClient).get_dynamic_quantum_architecture(other_calset_id).thenReturn(other_architecture)
    kwargs = create_run_request_default_kwargs | {'calibration_set_id': other_calset_id}
    when(IQMClient).create_run_request(ANY, **kwargs).thenReturn(run_request)
    when(IQMClient).submit_run_request(run_request).thenReturn(job_id)
    when(IQMClient).wait_for_results(job_id).thenReturn(
        RunResult(status=Status.READY, measurements=[{'some stuff': [[0], [1]]}], metadata=iqm_metadata)
    )

    sampler = IQMSampler(base_url)
    routed_circuit, _, _ = sampler.device.route_circuit(circuit_physical)
    other_sampler = IQMSampler(base_url, calibration_set_id=other_calset_id)

    with pytest.warns(
        UserWarning,
        match=re.escape(
            f'routed using calibration set(s) {set({adonis_architecture.calibration_set_id})}, '
            f'different than the current calibration set {other_calset_id}'
        ),
    ):
        other_sampler.run(routed_circuit)


@pytest.mark.usefixtures('unstub')
def test_run_iqm_batch(
    adonis_sampler, adonis_architecture, iqm_metadata, create_run_request_default_kwargs, job_id, run_request
):
    # pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals
    client = mock(IQMClient)
    repetitions = 123
    run_result = RunResult(
        status=Status.READY, measurements=[{'some stuff': [[0]]}, {'some stuff': [[1]]}], metadata=iqm_metadata
    )
    kwargs = create_run_request_default_kwargs | {'shots': repetitions}
    when(client).get_dynamic_quantum_architecture(None).thenReturn(adonis_architecture)
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
    base_url, adonis_architecture, iqm_metadata, create_run_request_default_kwargs, job_id, run_request
):
    # pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals
    client = mock(IQMClient)
    when(IQMClient).get_dynamic_quantum_architecture(None).thenReturn(adonis_architecture)
    run_result = RunResult(
        status=Status.READY, measurements=[{'some stuff': [[0]]}, {'some stuff': [[1]]}], metadata=iqm_metadata
    )
    timeout = 123
    sampler = IQMSampler(base_url, device=Adonis(), run_sweep_timeout=timeout)
    when(client).get_dynamic_quantum_architecture(None).thenReturn(adonis_architecture)
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
def test_credentials_are_passed_to_client(adonis_architecture):
    user_auth_args = {
        'auth_server_url': 'https://fake.auth.server.com',
        'username': 'fake-username',
        'password': 'fake-password',
    }
    mock_client = mock(IQMClient)
    when(module_under_test.iqm_sampler).IQMClient('http://url', client_signature=ANY, **user_auth_args).thenReturn(
        mock_client
    )
    when(mock_client).get_dynamic_quantum_architecture(None).thenReturn(adonis_architecture)
    IQMSampler('http://url', device=Adonis(), **user_auth_args)
    verify(module_under_test.iqm_sampler, times=1).IQMClient('http://url', client_signature=ANY, **user_auth_args)


@pytest.mark.usefixtures('unstub')
def test_client_signature_is_passed_to_client(adonis_architecture):
    """Test that IQMSampler set client signature"""
    when(IQMClient).get_dynamic_quantum_architecture(None).thenReturn(adonis_architecture)
    sampler = IQMSampler('http://some-url.iqm.fi', device=Adonis())
    assert f'cirq-iqm {version("cirq-iqm")}' in sampler._client._signature


@pytest.mark.usefixtures('unstub')
def test_close_client(adonis_architecture):
    user_auth_args = {
        'auth_server_url': 'https://fake.auth.server.com',
        'username': 'fake-username',
        'password': 'fake-password',
    }
    when(IQMClient).get_dynamic_quantum_architecture(None).thenReturn(adonis_architecture)
    sampler = IQMSampler('http://url', device=Adonis(), **user_auth_args)
    mock_client = mock(IQMClient)
    sampler._client = mock_client
    when(mock_client).close_auth_session().thenReturn(True)
    sampler.close_client()
    verify(mock_client, times=1).close_auth_session()


@pytest.mark.usefixtures('unstub')
def test_create_run_request_for_run(
    adonis_sampler, adonis_architecture, iqm_metadata, job_id, create_run_request_default_kwargs, run_request
):
    # pylint: disable=too-many-arguments,too-many-positional-arguments
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
    when(client).get_dynamic_quantum_architecture(None).thenReturn(adonis_architecture)
    when(client).submit_run_request(run_request).thenReturn(job_id)
    when(client).wait_for_results(job_id).thenReturn(run_result)

    assert adonis_sampler.create_run_request(circuit, repetitions=repetitions) == run_request
    adonis_sampler.run(circuit, repetitions=repetitions)

    verifyNoUnwantedInteractions()


@pytest.mark.usefixtures('unstub')
def test_create_run_request_for_run_iqm_batch(
    adonis_sampler, adonis_architecture, iqm_metadata, job_id, create_run_request_default_kwargs, run_request
):
    # pylint: disable=too-many-locals,too-many-arguments,too-many-positional-arguments
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
    when(client).get_dynamic_quantum_architecture(None).thenReturn(adonis_architecture)
    when(client).submit_run_request(run_request).thenReturn(job_id)
    when(client).wait_for_results(job_id).thenReturn(run_result)

    assert adonis_sampler.create_run_request(circuits, repetitions=repetitions) == run_request
    adonis_sampler.run_iqm_batch(circuits, repetitions=repetitions)

    verifyNoUnwantedInteractions()
