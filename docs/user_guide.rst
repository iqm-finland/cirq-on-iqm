.. _User guide:

User guide
==========

This guide serves as an introduction to the main features of Cirq on IQM. You are encouraged to run the demonstrated
code snippets and check the output yourself.


Installation
------------

The recommended way is to install the distribution package ``cirq-iqm`` directly from the Python Package Index (PyPI):

.. code-block:: bash

   $ pip install cirq-iqm


After installation Cirq on IQM can be imported in your Python code as follows:

.. code-block:: python

   import cirq_iqm


IQM's quantum devices
---------------------

Cirq on IQM provides descriptions of IQM's quantum architectures using the :class:`.IQMDevice` class, which is a
subclass of :class:`cirq.devices.Device` and implements general functionality relevant to all IQM devices. The native
gates and connectivity of the architecture are available in the :class:`.IQMDeviceMetadata` object returned by the
:attr:`.IQMDevice.metadata` property. It is possible to use the IQMDevice class directly, but
certain devices with predefined metadata are also available as subclasses of IQMDevice. As an example, let
us import the class :class:`.Adonis`, which describes IQM's five-qubit architecture, and view some of its
properties contained in its ``metadata`` property:

.. code-block:: python

    from cirq_iqm import Adonis

    adonis = Adonis()

    print(adonis.metadata.qubit_set)
    print(adonis.metadata.gateset)
    print(adonis.metadata.nx_graph)


IQM devices use :class:`cirq.NamedQubit` to represent their qubits. The names of the qubits consist of a prefix
followed by a numeric index, so we have qubit names like ``QB1``, ``QB2``, etc. Note that we use 1-based
indexing. You can get the list of the qubits in a particular device by accessing the :attr:`qubits` attribute of a
corresponding :class:`.IQMDevice` instance:

.. code-block:: python

    print(adonis.qubits)


Constructing circuits
---------------------

There are two main workflows of using :class:`cirq.Circuit` instances with IQM devices:

1. Create a ``Circuit`` instance, use arbitrary qubit names and types. There is no
   validation of the operations when appending. At any point the user can apply :meth:`.IQMDevice.decompose_circuit`
   to decompose the circuit contents into the native operation set of the device, or :meth:`.IQMDevice.route_circuit`
   to route the circuit to the device connectivity and device qubits.
2. Create a ``Circuit`` from an OpenQASM 2.0 program. The qubit names are determined by the OpenQASM ``qreg`` names,
   appended with zero-based indices. Proceed as in workflow 1.

Below we demonstrate examples of creating circuits in each of the two workflows.

.. _workflow_1:

Workflow 1
^^^^^^^^^^

Construct a circuit and use arbitrary qubits:

.. code-block:: python

    import cirq

    q1, q2 = cirq.NamedQubit('Alice'), cirq.NamedQubit('Bob')
    circuit_1 = cirq.Circuit()
    circuit_1.append(cirq.X(q1))
    circuit_1.append(cirq.H(q2))
    circuit_1.append(cirq.CNOT(q1, q2))
    circuit_1.append(cirq.measure(q1, q2, key='m'))
    print(circuit_1)

This will result in the circuit
::

   Alice: ───X───@───M('m')───
                 │   │
   Bob: ─────H───X───M────────

After the circuit has been constructed, it can be decomposed and routed against a particular ``IQMDevice``.
The method :meth:`.IQMDevice.decompose_circuit` accepts a :class:`cirq.Circuit` object as an argument and
returns the decomposed circuit containing only native gates for the corresponding device:

.. code-block:: python

    decomposed_circuit_1 = adonis.decompose_circuit(circuit_1)


The method :meth:`.IQMDevice.route_circuit` accepts a :class:`cirq.Circuit` object as an argument,
and returns the circuit routed against the device, acting on the device qubits instead of the
arbitrary qubits we had originally.

.. code-block:: python

    routed_circuit_1 = adonis.route_circuit(decomposed_circuit_1)
    print(routed_circuit_1)


::

    QB3: ───X────────────────────@───────────M('m')───
                                 │           │
    QB4: ───Y^0.5───X───Y^-0.5───@───Y^0.5───M────────

By default :meth:`.route_circuit` returns only the routed circuit. However if you set its keyword
argument ``return_swap_network`` to ``True``, it will return the full
:class:`cirq.contrib.routing.swap_network.SwapNetwork` object which contains the routed
circuit itself and the mapping between the used device qubits and the original ones.

Under the hood, :meth:`.route_circuit` leverages the routing algorithm in :mod:`cirq.contrib.routing.router`.
It works on single- and two-qubit gates, and measurement operations of arbitrary size.
If you have gates involving more than two qubits you need to decompose them before routing.
Since routing may add some SWAP gates to the circuit, you will need to decompose the circuit
again after the routing, unless SWAP is a native gate for the target device.

Yet another important topic is circuit optimization. In addition to the optimizers available in Cirq you can also
benefit from Cirq on IQM's :mod:`.optimizers` module which contains some optimization tools geared towards IQM devices.
The function :func:`.optimizers.simplify_circuit` is a convenience method encapsulating a particular sequence of
optimizations. Let us try it out on our decomposed and routed circuit above:

.. code-block:: python

    from cirq_iqm.optimizers import simplify_circuit

    simplified_circuit_1 = simplify_circuit(routed_circuit_1)
    print(simplified_circuit_1)


::

    QB3: ───PhX(1)───@───────────────────M('m')───
                     │                   │
    QB5: ────────────@───PhX(-0.5)^0.5───M────────


.. note::

    The funtion :func:`.simplify_circuit` is not associated with any IQM device, so its result may contain non-native
    gates for a particular device. In the example above we don't have them, however it is generally a good idea to run
    decomposition once again after the simplification.


Workflow 2
^^^^^^^^^^

You can read an OpenQASM 2.0 program from a file (or a string), e.g.

::

   OPENQASM 2.0;
   include "qelib1.inc";

   qreg q[2];
   creg m[2];

   x q[0];
   h q[1];
   cx q[0], q[1];
   measure q -> m;

and convert it into a :class:`cirq.Circuit` object using :func:`.circuit_from_qasm`.
Once you have done this, you can perform the decomposition and routing steps as in
the previous workflow to prepare the circuit for execution on an IQM device.

.. code-block:: python

    import cirq_iqm

    with open('circuit.qasm', 'r') as f:
        circuit_2 = cirq_iqm.circuit_from_qasm(f.read())
    print(circuit_2)

::

   q_0: ───X───@───M('m_0')───
               │
   q_1: ───H───X───M('m_1')───

:func:`.circuit_from_qasm` uses the OpenQASM 2.0 parser in :mod:`cirq.contrib.qasm_import`.


Running on a real quantum computer
----------------------------------

.. note::

   At the moment IQM does not provide a quantum computing service open to the general public.
   Please contact our `sales team <https://www.meetiqm.com/contact/>`_ to set up your access to an IQM quantum computer.

Cirq contains various simulators which you can use to simulate the circuits constructed above.
In this subsection we demonstrate how to run them on an IQM quantum computer.

Cirq on IQM implements :class:`.IQMSampler`, a subclass of :class:`cirq.work.Sampler`, which is used
to execute quantum circuits. Once you have access to an IQM server you can create an :class:`.IQMSampler`
instance and use its :meth:`~.IQMSampler.run` method to send a circuit for execution and retrieve the results:

.. code-block:: python

   from cirq_iqm.iqm_sampler import IQMSampler

   sampler = IQMSampler(iqm_server_url)
   result = sampler.run(circuit_1, repetitions=10)
   print(result.measurements['m'])


Note that the code snippet above assumes that you have set the variable ``iqm_server_url`` to the URL
of the IQM server. By default, the latest calibration set is used for running the circuit. If you want to use
a particular calibration set, provide the ``calibration_set_id`` argument. The sampler will by default use an
:class:`.IQMDevice` created based on architecture data obtained from the server, which is then available in the
:attr:`.IQMSampler.device` property. Alternatively, the device can be specified directly with the ``device`` argument.

If the IQM server you are connecting to requires authentication, you will also have to use
`Cortex CLI <https://github.com/iqm-finland/cortex-cli>`_ to retrieve and automatically refresh access tokens,
then set the ``IQM_TOKENS_FILE`` environment variable to use those tokens.
See Cortex CLI's `documentation <https://iqm-finland.github.io/cortex-cli/readme.html>`_ for details.
Alternatively, authorize with the IQM_AUTH_SERVER, IQM_AUTH_USERNAME and IQM_AUTH_PASSWORD environment variables
or pass them as arguments to the constructor of :class:`.IQMProvider`, however this approach is less secure
and considered deprecated.

When executing a circuit that uses something other than the device qubits, you need to either route it first
as explained in :ref:`workflow 1 <workflow_1>` above,
or provide the mapping from the *logical* qubits in the circuit to the *physical* qubits on the device yourself.
The initializer of :class:`.IQMSampler` accepts an optional argument called ``qubit_mapping`` which
can be used to specify this correspondence.

.. code-block:: python

    import json


    qubit_mapping = {'Alice': 'QB1', 'Bob': 'QB3'}

    sampler = IQMSampler(iqm_server_url, qubit_mapping=qubit_mapping)
    result = sampler.run(decomposed_circuit_1, repetitions=10)
    print(result.measurements['m'])



More examples
-------------

More examples are available in the
`examples directory <https://github.com/iqm-finland/cirq-on-iqm/tree/main/examples>`_
of the Cirq on IQM repository.


.. include:: ../DEVELOPMENT.rst
