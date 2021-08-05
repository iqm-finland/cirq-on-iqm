.. _Getting started:

Getting started with Cirq on IQM
================================

This guide describes how to install and use Cirq on IQM.

Installation
------------

The recommended way is to install the distribution package ``cirq-iqm`` directly from the
Python Package Index (PyPI):

.. code-block:: bash

   $ pip install cirq-iqm


Alternatively, you can clone the `github repository <https://github.com/iqm-finland/cirq-on-iqm>`_,
then build and install the distribution package yourself (Note the trailing slash to install from the local directory):

.. code-block:: bash

   $ git clone git@github.com:iqm-finland/cirq-on-iqm.git
   $ pip install cirq-on-iqm/


After installation Cirq on IQM can be imported in your Python code as follows:

.. code-block:: python

   import cirq_iqm


IQM's quantum devices
---------------------

Cirq on IQM provides descriptions of IQM's quantum architectures by providing various subclasses of
Cirq's :code:`cirq.devices.Device` class. As an example, let us import the class :code:`Adonis`,
which describes IQM's five-qubit architecture and view the native gates and the qubit connectivity:

.. code-block:: python

    from cirq_iqm import Adonis

    print(Adonis.NATIVE_GATES)
    print(Adonis.CONNECTIVITY)


Note that the qubits in the Adonis architecture are numbered from 1 to 5.


Constructing circuits with Cirq
-------------------------------

Construct a quantum circuit against the adonis architecture

.. code-block:: python

    import cirq

    adonis = Adonis()
    qb_1, qb_2 = adonis.qubits[:2]
    circuit = cirq.Circuit(device=adonis)
    circuit.append(cirq.X(qb_1))
    circuit.append(cirq.H(qb_2))
    circuit.append(cirq.measurement(qb_1, qb_2, key='mk'))


Running on a real quantum computer
----------------------------------

To execute a quantum circuit on an IQM quantum computer you need to have access to IQM server. You will need
to setup two environment variables: :code:`IQM_SERVER_URL`, which points to the respective IQM server; and
:code:`IQM_SETTINGS_PATH` which points to a local file containing configuration settings for the device:

.. code-block:: bash

   $ export IQM_SERVER_URL="https://example.com"
   $ export IQM_SETTINGS_PATH="/path/to/settings.json"


Once you have these, you can use the :code:`IQMSampler` shipped with Cirq on IQM to send the circuit for execution

.. code-block:: python

    with open(os.environ['IQM_SETTINGS_PATH'], 'r') as f:
        sampler = IQMSampler(os.environ['IQM_SERVER_URL'], f.read(), qubit_mapping)


More examples
-------------

More examples are available in the `examples directory <https://github.com/iqm-finland/cirq-on-iqm/tree/main/examples>`_ of the github repository.


.. include:: ../DEVELOPMENT.rst