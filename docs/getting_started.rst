Getting started with Cirq on IQM
================================

This guide describes how to install and use Cirq on IQM.

Installation
------------

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


How to use
----------

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
--------------

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
