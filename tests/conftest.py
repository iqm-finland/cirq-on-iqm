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
from iqm.iqm_client import DynamicQuantumArchitecture, GateImplementationInfo, GateInfo

existing_run = UUID('3c3fcda3-e860-46bf-92a4-bcc59fa76ce9')
missing_run = UUID('059e4186-50a3-4e6c-ba1f-37fe6afbdfc2')


@pytest.fixture()
def base_url():
    return 'https://example.com'


@pytest.fixture
def fake_arch_with_resonator():
    return DynamicQuantumArchitecture(
        calibration_set_id=UUID('26c5e70f-bea0-43af-bd37-6212ec7d04cb'),
        qubits=['QB1', 'QB2', 'QB3', 'QB4', 'QB5', 'QB6'],
        computational_resonators=['COMP_R'],
        gates={
            'prx': GateInfo(
                implementations={
                    'drag_gaussian': GateImplementationInfo(
                        loci=(('QB1',), ('QB2',), ('QB3',), ('QB4',), ('QB5',), ('QB6',))
                    ),
                },
                default_implementation='drag_gaussian',
                override_default_implementation={},
            ),
            'cz': GateInfo(
                implementations={
                    'tgss': GateImplementationInfo(
                        loci=(
                            ('QB1', 'COMP_R'),
                            ('QB2', 'COMP_R'),
                            ('QB3', 'COMP_R'),
                            ('QB4', 'COMP_R'),
                            ('QB5', 'COMP_R'),
                            ('QB6', 'COMP_R'),
                        )
                    ),
                },
                default_implementation='tgss',
                override_default_implementation={},
            ),
            'move': GateInfo(
                implementations={
                    'tgss_crf': GateImplementationInfo(
                        loci=(
                            ('QB1', 'COMP_R'),
                            ('QB2', 'COMP_R'),
                            ('QB3', 'COMP_R'),
                            ('QB4', 'COMP_R'),
                            ('QB5', 'COMP_R'),
                        )
                    ),
                },
                default_implementation='tgss_crf',
                override_default_implementation={},
            ),
            'measure': GateInfo(
                implementations={
                    'constant': GateImplementationInfo(
                        loci=(('QB1',), ('QB2',), ('QB3',), ('QB4',), ('QB5',), ('QB6',))
                    ),
                },
                default_implementation='constant',
                override_default_implementation={},
            ),
        },
    )


@pytest.fixture
def adonis_architecture_shuffled_names():
    return DynamicQuantumArchitecture(
        calibration_set_id=UUID('26c5e70f-bea0-43af-bd37-6212ec7d04cb'),
        qubits=['QB2', 'QB3', 'QB1', 'QB5', 'QB4'],
        computational_resonators=[],
        gates={
            'prx': GateInfo(
                implementations={
                    'drag_gaussian': GateImplementationInfo(loci=(('QB2',), ('QB3',), ('QB1',), ('QB5',), ('QB4',))),
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
                    'constant': GateImplementationInfo(loci=(('QB2',), ('QB3',), ('QB1',), ('QB5',), ('QB4',)))
                },
                default_implementation='constant',
                override_default_implementation={},
            ),
        },
    )


@pytest.fixture()
def device_without_resonator(adonis_architecture_shuffled_names):
    """Returns device object created based on architecture specification"""
    return IQMDevice(IQMDeviceMetadata.from_architecture(adonis_architecture_shuffled_names))


@pytest.fixture()
def device_with_resonator(fake_arch_with_resonator):
    """Returns device object created based on architecture specification"""
    return IQMDevice(IQMDeviceMetadata.from_architecture(fake_arch_with_resonator))


@pytest.fixture
def device_with_multiple_resonators():
    """Some fictional 5 qubit device with multiple resonators."""
    multiple_resonators_arch = DynamicQuantumArchitecture(
        calibration_set_id=UUID('26c5e70f-bea0-43af-bd37-6212ec7d04cb'),
        qubits=['QB1', 'QB2', 'QB3', 'QB4', 'QB5'],
        computational_resonators=['COMP_R0', 'COMP_R1', 'COMP_R2', 'COMP_R3', 'COMP_R4'],
        gates={
            'prx': GateInfo(
                implementations={
                    'drag_gaussian': GateImplementationInfo(loci=(('QB2',), ('QB3',), ('QB1',), ('QB5',), ('QB4',))),
                },
                default_implementation='drag_gaussian',
                override_default_implementation={},
            ),
            'cz': GateInfo(
                implementations={
                    'tgss': GateImplementationInfo(
                        loci=(
                            ('QB1', 'COMP_R0'),
                            ('QB2', 'COMP_R0'),
                            ('QB2', 'COMP_R1'),
                            ('QB3', 'COMP_R1'),
                            ('QB3', 'COMP_R2'),
                            ('QB4', 'COMP_R2'),
                            ('QB4', 'COMP_R3'),
                            ('QB5', 'COMP_R3'),
                            ('QB5', 'COMP_R4'),
                            ('QB1', 'COMP_R4'),
                            ('QB1', 'QB3'),
                        )
                    ),
                },
                default_implementation='tgss',
                override_default_implementation={},
            ),
            'move': GateInfo(
                implementations={
                    'tgss_crf': GateImplementationInfo(
                        loci=(
                            ('QB1', 'COMP_R0'),
                            ('QB2', 'COMP_R1'),
                            ('QB3', 'COMP_R2'),
                            ('QB4', 'COMP_R3'),
                            ('QB5', 'COMP_R4'),
                        )
                    ),
                },
                default_implementation='tgss_crf',
                override_default_implementation={},
            ),
            'measure': GateInfo(
                implementations={
                    'constant': GateImplementationInfo(loci=(('QB2',), ('QB3',), ('QB1',), ('QB5',), ('QB4',))),
                },
                default_implementation='constant',
                override_default_implementation={},
            ),
        },
    )
    return IQMDevice(IQMDeviceMetadata.from_architecture(multiple_resonators_arch))
