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
from cirq_iqm import Adonis, Apollo, Valkmusa


def test_equality_method():
    adonis_1 = Adonis()
    adonis_2 = Adonis()
    adonis_3 = Adonis()
    apollo_1 = Apollo()
    apollo_2 = Apollo()
    valkmusa = Valkmusa()
    adonis_3._metadata = valkmusa.metadata

    assert adonis_1 == adonis_2
    assert valkmusa != adonis_1
    assert apollo_1 == apollo_2
    assert adonis_2 != adonis_3
