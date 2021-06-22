Cirq on IQM
###########

:Release: |release|
:Date: |today|


`Google Cirq <https://github.com/quantumlib/Cirq>`_ descriptions of IQM's quantum architectures.


Features
--------

Currently Cirq on IQM can

* load an arbitrary quantum circuit from a QASM file
* map it into an equivalent circuit compatible with the chosen IQM architecture
* optimize the circuit by commuting and merging gates
* simulate the circuit using one of Cirq's simulators

See the :download:`Jupyter Notebook with examples <usage.ipynb>`.

Run the demo:

.. code-block:: bash

   python examples/adonis_demo.py


Contents
--------

.. toctree::
   :maxdepth: 2

   API
   license
   authors
   changelog


Indices
=======

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
