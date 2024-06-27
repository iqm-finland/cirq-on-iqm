# Copyright 2020–2021 Cirq on IQM developers
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Mocks server calls for testing
"""

from uuid import UUID

import pytest

from iqm.cirq_iqm import IQMDevice, IQMDeviceMetadata
from iqm.iqm_client import QuantumArchitectureSpecification

existing_run = UUID('3c3fcda3-e860-46bf-92a4-bcc59fa76ce9')
missing_run = UUID('059e4186-50a3-4e6c-ba1f-37fe6afbdfc2')


@pytest.fixture()
def base_url():
    return 'https://example.com'


@pytest.fixture()
def fake_spec_with_resonator():
    ndonis_architecture_specification = {
        'name': 'Ndonis',
        'operations': {
            'cz': [
                ['QB1', 'COMP_R'],
                ['QB2', 'COMP_R'],
                ['QB3', 'COMP_R'],
                ['QB4', 'COMP_R'],
                ['QB5', 'COMP_R'],
                ['QB6', 'COMP_R'],
            ],
            'prx': [['QB1'], ['QB2'], ['QB3'], ['QB4'], ['QB5'], ['QB6']],
            'move': [
                ['QB1', 'COMP_R'],
                ['QB2', 'COMP_R'],
                ['QB3', 'COMP_R'],
                ['QB4', 'COMP_R'],
                ['QB5', 'COMP_R'],
            ],
            'barrier': [],
            'measure': [['QB1'], ['QB2'], ['QB3'], ['QB4'], ['QB5'], ['QB6']],
        },
        'qubits': ['COMP_R', 'QB1', 'QB2', 'QB3', 'QB4', 'QB5', 'QB6'],
        'qubit_connectivity': [
            ['QB1', 'COMP_R'],
            ['QB2', 'COMP_R'],
            ['QB3', 'COMP_R'],
            ['QB4', 'COMP_R'],
            ['QB5', 'COMP_R'],
            ['QB6', 'COMP_R'],
        ],
    }
    return QuantumArchitectureSpecification(**ndonis_architecture_specification)


@pytest.fixture
def adonis_architecture_shuffled_names():
    return QuantumArchitectureSpecification(
        name='Adonis',
        operations={
            'prx': [['QB2'], ['QB3'], ['QB1'], ['QB5'], ['QB4']],
            'cz': [['QB1', 'QB3'], ['QB2', 'QB3'], ['QB4', 'QB3'], ['QB5', 'QB3']],
            'measure': [['QB2'], ['QB3'], ['QB1'], ['QB5'], ['QB4']],
            'barrier': [],
        },
        qubits=['QB2', 'QB3', 'QB1', 'QB5', 'QB4'],
        qubit_connectivity=[['QB1', 'QB3'], ['QB2', 'QB3'], ['QB4', 'QB3'], ['QB5', 'QB3']],
    )


@pytest.fixture()
def device_without_resonator(adonis_architecture_shuffled_names):
    """Returns device object created based on architecture specification"""
    return IQMDevice(IQMDeviceMetadata.from_architecture(adonis_architecture_shuffled_names))


@pytest.fixture()
def device_with_resonator(fake_spec_with_resonator):
    """Returns device object created based on architecture specification"""
    return IQMDevice(IQMDeviceMetadata.from_architecture(fake_spec_with_resonator))


@pytest.fixture
def device_with_multiple_resonators():
    """Some fictional 5 qubit device with multiple resonators."""
    multiple_resonators_specification = {
        'name': 'MultiResonators',
        'operations': {
            'cz': [
                ['QB1', 'COMP_R0'],
                ['QB2', 'COMP_R0'],
                ['QB2', 'COMP_R1'],
                ['QB3', 'COMP_R1'],
                ['QB3', 'COMP_R2'],
                ['QB4', 'COMP_R2'],
                ['QB4', 'COMP_R3'],
                ['QB5', 'COMP_R3'],
                ['QB5', 'COMP_R4'],
                ['QB1', 'COMP_R4'],
                ['QB1', 'QB3'],
            ],
            'prx': [['QB2'], ['QB3'], ['QB1'], ['QB5'], ['QB4']],
            'move': [
                ['QB1', 'COMP_R0'],
                ['QB2', 'COMP_R1'],
                ['QB3', 'COMP_R2'],
                ['QB4', 'COMP_R3'],
                ['QB5', 'COMP_R4'],
            ],
            'barrier': [],
            'measure': [['QB2'], ['QB3'], ['QB1'], ['QB5'], ['QB4']],
        },
        'qubits': ['COMP_R0', 'COMP_R1', 'COMP_R2', 'COMP_R3', 'COMP_R4', 'QB1', 'QB2', 'QB3', 'QB4', 'QB5'],
        'qubit_connectivity': [
            ['QB1', 'COMP_R0'],
            ['QB2', 'COMP_R0'],
            ['QB2', 'COMP_R1'],
            ['QB3', 'COMP_R1'],
            ['QB3', 'COMP_R2'],
            ['QB4', 'COMP_R2'],
            ['QB4', 'COMP_R3'],
            ['QB5', 'COMP_R3'],
            ['QB5', 'COMP_R4'],
            ['QB1', 'COMP_R4'],
            ['QB1', 'QB3'],
        ],
    }
    return IQMDevice(
        IQMDeviceMetadata.from_architecture(QuantumArchitectureSpecification(**multiple_resonators_specification))
    )
