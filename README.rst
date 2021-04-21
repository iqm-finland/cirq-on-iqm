Cirq on IQM
###########

`Google Cirq <https://github.com/quantumlib/Cirq>`_ adapter for IQM's quantum architectures.


What is it good for?
====================

Currently Cirq on IQM can

* load an arbitrary quantum circuit from a QASM file
* map it into an equivalent circuit compatible with the chosen IQM architecture
* optimize the circuit by commuting and merging gates
* simulate the circuit using one of Cirq's simulators

See the `Jupyter Notebook with examples <docs/usage.ipynb>`_.


How to use in another project
=============================

The recommended way is to install the distribution package ``cirq-iqm`` directly from the
Python Package Index (PyPI). You can either add ``cirq-iqm`` as a dependency to your project
using ``setup.cfg``, or install it manually:

.. code-block:: bash

   pip install cirq-iqm


Alternatively, you can clone the repository, and build and install the distribution package yourself.
Note the trailing slash to install from the local directory.

.. code-block:: bash

   git clone git@github.com:iqm-finland/cirq-on-iqm.git
   pip install cirq-on-iqm/


Import the module in your Python code:

.. code-block:: python

   import cirq_iqm


Run the demo:

.. code-block:: bash

   python cirq-on-iqm/examples/demo_adonis.py


Running a Jupyter notebook in virtualenv takes a bit of extra work,
you will need to create a custom Jupyter kernel for your virtual environment:

.. code-block:: bash

   virtualenv my_virtualenv
   source my_virtualenv/bin/activate
   pip install --user ipykernel
   python -m ipykernel install --user --name=my_virtualenv


How to develop
==============

Clone the repository and install it in editable mode with all the extras:

.. code-block:: bash

   git clone git@github.com:iqm-finland/cirq-on-iqm.git
   cd cirq-on-iqm
   pip install -e ".[dev,docs]"


Build and view the docs:

.. code-block:: bash

   python setup.py docs
   firefox build/sphinx/html/index.html


Run the tests:

.. code-block:: bash

   tox


Copyright
=========

Cirq on IQM is free software, released under the Apache License, version 2.0.

Copyright 2020–2021 Cirq on IQM developers.
