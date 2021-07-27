|CI badge|

.. |CI badge| image:: https://github.com/iqm-finland/cirq-on-iqm/actions/workflows/ci.yml/badge.svg

Cirq on IQM
###########

`Google Cirq <https://github.com/quantumlib/Cirq>`_ adapter for IQM's quantum architectures.


What is it good for?
====================

Currently Cirq on IQM can

* take an arbitrary quantum circuit created in Cirq or load from an OpenQASM 2.0 file
* map the circuit into an equivalent one compatible with the chosen IQM quantum architecture
* optimize the circuit by commuting and merging gates
* simulate the circuit using one of Cirq's simulators
* run the circuit on an IQM quantum computer

See the `Jupyter Notebook <https://jupyter.org/>`_ with examples: ``examples/usage.ipynb``.


How to use
==========

The recommended way is to install the distribution package ``cirq-iqm`` directly from the
Python Package Index (PyPI). You can either add ``cirq-iqm`` as a dependency to your project
using ``setup.cfg``, or install it manually:

.. code-block:: bash

   $ pip install cirq-iqm


Alternatively, you can clone the repository, and build and install the distribution package yourself.
Note the trailing slash to install from the local directory.

.. code-block:: bash

   $ git clone git@github.com:iqm-finland/cirq-on-iqm.git
   $ pip install cirq-on-iqm/


Import the module in your Python code:

.. code-block:: python

   import cirq_iqm


Run the demo:

.. code-block:: bash

   $ python cirq-on-iqm/examples/demo_adonis.py


Run code on a real quantum computer:

.. code-block:: bash

   $ export IQM_SERVER_URL="https://example.com"
   $ export IQM_SETTINGS_PATH="/path/to/settings.json"
   $ python cirq-on-iqm/examples/demo_iqm_execution.py


How to develop
==============

Clone the repository and install it in editable mode with all the extras:

.. code-block:: bash

   $ git clone git@github.com:iqm-finland/cirq-on-iqm.git
   $ cd cirq-on-iqm
   $ pip install -e ".[dev,docs,testing]"


Build and view the docs:

.. code-block:: bash

   $ tox -e docs
   $ firefox build/sphinx/html/index.html


Run the tests:

.. code-block:: bash

   $ tox


Copyright
=========

Cirq on IQM is free software, released under the Apache License, version 2.0.

Copyright 2020–2021 Cirq on IQM developers.
