.. _User guide:

User guide
==========


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
which describes IQM's five-qubit architecture and view some of its properties contained in the class variables:

.. code-block:: python

    from cirq_iqm import Adonis

    print(Adonis.QUBIT_COUNT)
    print(Adonis.NATIVE_GATES)
    print(Adonis.CONNECTIVITY)


Note that the qubits are indexed starting from 1.


Constructing circuits
---------------------

There are three main ways of using :class:`Circuits <cirq.Circuit>` with :class:`.IQMDevice`.

1. Create a Circuit instance associated with an IQMDevice, and use only the device qubits.
   Each :class:`cirq.Operation` is validated (qubits are on the device, and properly connected) and decomposed as
   soon as it is appended to the circuit. No routing is possible, the user has to take care of it.
2. Create a Circuit instance with no associated device. Use arbitrary qubits, there is no
   validation of the ops when appended. At any point the user can apply :meth:`.IQMDevice.decompose_circuit`
   to decompose the Circuit contents into the native set of the device, or :meth:`.IQMDevice.route_circuit`
   to route the circuit to the device connectivity.
   The qubit/connectivity check is only done at :class:`.IQMSampler` using the given ``qubit_map``.
3. Create a Circuit from an OpenQASM 2.0 program, qubits will have names like ``q_0`` with zero-based
   indexing. Proceed as in workflow 2.


Construct a quantum circuit against the Adonis architecture

.. code-block:: python

    import cirq

    adonis = Adonis()
    qb_1, qb_2 = adonis.qubits[:2]
    circuit = cirq.Circuit(device=adonis)
    circuit.append(cirq.X(qb_1))
    circuit.append(cirq.H(qb_2))
    circuit.append(cirq.measure(qb_1, qb_2, key='mk'))


An arbitrary cirq circuit

.. code-block:: python

    import cirq

    qb_1, qb_2 = cirq.NamedQubit('Alice'), cirq.NamedQuibt('Bob')
    circuit = cirq.Circuit()
    circuit.append(cirq.X(qb_1))
    circuit.append(cirq.H(qb_2))
    circuit.append(cirq.measure(qb_1, qb_2, key='mk'))


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