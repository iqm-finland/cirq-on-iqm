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

   from iqm import cirq_iqm


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

    from iqm.cirq_iqm import Adonis

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

There are two main ways of constructing :class:`cirq.Circuit` instances for IQM devices:

1. Create a ``Circuit`` instance using arbitrary qubit names and types.
2. Create a ``Circuit`` from an OpenQASM 2.0 program. The qubit names are determined by the OpenQASM ``qreg`` names,
   appended with zero-based indices.

Below we give an example of each method.


Method 1
^^^^^^^^

Construct a circuit and use arbitrary qubits:

.. code-block:: python

    import cirq

    q1, q2 = cirq.NamedQubit('Alice'), cirq.NamedQubit('Bob')
    circuit = cirq.Circuit()
    circuit.append(cirq.X(q1))
    circuit.append(cirq.H(q2))
    circuit.append(cirq.CNOT(q1, q2))
    circuit.append(cirq.measure(q1, q2, key='m'))
    print(circuit)

This will result in the circuit
::

   Alice: ───X───@───M('m')───
                 │   │
   Bob: ─────H───X───M────────


Method 2
^^^^^^^^

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

.. code-block:: python

    from iqm import cirq_iqm

    with open('circuit.qasm', 'r') as f:
        qasm_circuit = cirq_iqm.circuit_from_qasm(f.read())
    print(qasm_circuit)

::

   q_0: ───X───@───M('m_0')───
               │
   q_1: ───H───X───M('m_1')───

:func:`.circuit_from_qasm` uses the OpenQASM 2.0 parser in :mod:`cirq.contrib.qasm_import`.

After a circuit has been constructed, it can be decomposed and routed against a particular ``IQMDevice``.


Decomposition
-------------

The method :meth:`.IQMDevice.decompose_circuit` accepts a :class:`cirq.Circuit` object as an argument and
returns the decomposed circuit containing only native operations for the corresponding device:

.. code-block:: python

    decomposed_circuit = adonis.decompose_circuit(circuit)
    print(decomposed_circuit)

::

    Alice: ───X────────────────────@───────────M('m')───
                                   │           │
    Bob: ─────Y^0.5───X───Y^-0.5───@───Y^0.5───M────────

The Hadamard and CNOT gates are not native to Adonis, so they were decomposed to X, Y and CZ gates which are.


.. _routing:

Routing
-------

Routing means transforming a circuit such that it acts on the device qubits, and respects the
device connectivity.
The method :meth:`.IQMDevice.route_circuit` accepts a :class:`cirq.Circuit` object as an argument,
and returns the circuit routed against the device, acting on the device qubits instead of the
arbitrary qubits we had originally.

.. code-block:: python

    routed_circuit_1, initial_mapping, final_mapping = adonis.route_circuit(decomposed_circuit)
    print(routed_circuit_1)

::

    QB3: ───X────────────────────@───────────M('m')───
                                 │           │
    QB4: ───Y^0.5───X───Y^-0.5───@───Y^0.5───M────────

Along with the routed circuit :meth:`.route_circuit` returns the ``initial_mapping`` and ``final_mapping``.
The ``initial_mapping`` is either the mapping from circuit to device qubits as provided by an
:class:`cirq.AbstractInitialMapper` or a mapping that is initialized from the device graph.
The ``final_mapping`` is the mapping from physical qubits before inserting SWAP gates to the physical
qubits after the routing is complete

As mentioned above, you may also provide the initial mapping from the *logical* qubits in the circuit to the
*physical* qubits on the device yourself, by using the keyword argument ``initial_mapper``.
It serves as the starting point of the routing:

.. code-block:: python

    initial_mapper = cirq.HardCodedInitialMapper({q1: adonis.qubits[2], q2: adonis.qubits[0]})
    routed_circuit_2, _, _ = adonis.route_circuit(
        decomposed_circuit,
        initial_mapper=initial_mapper,
    )
    print(routed_circuit_2)

::

    QB1: ───Y^0.5───X───Y^-0.5───@───Y^0.5───────M────────
                                 │               │
    QB3: ───X────────────────────@───────────────M('m')───

Under the hood, :meth:`.route_circuit` leverages the routing provided by :class:`cirq.RouteCQC`.
It works on single- and two-qubit gates, and measurement operations of arbitrary size.
If you have gates involving more than two qubits you need to decompose them before routing.
Since routing may add some SWAP gates to the circuit, you will need to decompose the circuit
again after the routing, unless SWAP is a native gate for the target device.


Optimization
------------

Yet another important topic is circuit optimization. In addition to the optimizers available in Cirq you can also
benefit from Cirq on IQM's :mod:`.optimizers` module which contains some optimization tools geared towards IQM devices.
The function :func:`.optimizers.simplify_circuit` is a convenience method encapsulating a particular sequence of
optimizations. Let us try it out on our decomposed and routed circuit above:

.. code-block:: python

    from iqm.cirq_iqm.optimizers import simplify_circuit

    simplified_circuit = simplify_circuit(routed_circuit_1)
    print(simplified_circuit)


::

    QB3: ───PhX(1)───@───────────────────M('m')───
                     │                   │
    QB4: ────────────@───PhX(-0.5)^0.5───M────────


.. note::

    The funtion :func:`.simplify_circuit` is not associated with any IQM device, so its result may contain non-native
    gates for a particular device. In the example above we don't have them, however it is generally a good idea to run
    decomposition once again after the simplification.



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

   from iqm.cirq_iqm.iqm_sampler import IQMSampler

   sampler = IQMSampler(iqm_server_url)
   result = sampler.run(routed_circuit_1, repetitions=10)
   print(result.measurements['m'])


Note that the code snippet above assumes that you have set the variable ``iqm_server_url`` to the URL
of the IQM server. Additionally, you can pass IQM backend specific options to the :class:`.IQMSampler` class.
The below table summarises the currently available options:


.. list-table::
   :widths: 25 20 25 100
   :header-rows: 1

   * - Name
     - Type
     - Example value
     - Description
   * - `calibration_set_id`
     - str
     - "f7d9642e-b0ca-4f2d-af2a-30195bd7a76d"
     - Indicates the calibration set to use. Defaults to `None`, which means the IQM server will use the best
       available calibration set automatically.
   * - `circuit_duration_check`
     - bool
     - False
     - Enable or disable server-side circuit duration checks. The default value is `True`, which means if any job is
       estimated to take unreasonably long compared to the coherence times of the qubits, or too long in wall-clock
       time, the server will reject it. This option can be used to disable this behaviour. In normal use, the
       circuit duration check should always remain enabled.
   * - `heralding_mode`
     - :py:class:`~iqm_client.iqm_client.HeraldingMode`
     - "zeros"
     - Heralding mode to use during execution. The default value is "none", "zeros" enables heralding.

For example if you would like to use a particular calibration set, you can provide it as follows:

.. code-block:: python

   sampler = IQMSampler(iqm_server_url, calibration_set_id="f7d9642e-b0ca-4f2d-af2a-30195bd7a76d")


The same applies for `heralding_mode` and `circuit_duration_check`. The sampler will by default use an
:class:`.IQMDevice` created based on architecture data obtained from the server, which is then available in the
:attr:`.IQMSampler.device` property. Alternatively, the device can be specified directly with the ``device`` argument.

If the IQM server you are connecting to requires authentication, you will also have to use
`Cortex CLI <https://github.com/iqm-finland/cortex-cli>`_ to retrieve and automatically refresh access tokens,
then set the ``IQM_TOKENS_FILE`` environment variable to use those tokens.
See Cortex CLI's `documentation <https://iqm-finland.github.io/cortex-cli/readme.html>`_ for details.
Alternatively, you can authenticate yourself using the ``IQM_AUTH_SERVER``, ``IQM_AUTH_USERNAME``
and ``IQM_AUTH_PASSWORD`` environment variables, or pass them as arguments to the constructor of
:class:`.IQMProvider`, but this approach is less secure and considered deprecated.

When executing a circuit that uses something other than the device qubits, you need to route it first,
as explained in the :ref:`routing` section above.

Multiple circuits can be submitted to the IQM quantum computer at once using the :meth:`~.IQMSampler.run_iqm_batch` method of :class:`.IQMSampler`.
This is often faster than executing the circuits individually. Circuits submitted in a batch are still executed sequentially.

.. code-block:: python

   circuit_list = []

   circuit_list.append(routed_circuit_1)
   circuit_list.append(routed_circuit_2)

   results = sampler.run_iqm_batch(circuit_list, repetitions=10)

   for result in results:
        print(result.histogram(key="m"))


More examples
-------------

More examples are available in the
`examples directory <https://github.com/iqm-finland/cirq-on-iqm/tree/main/examples>`_
of the Cirq on IQM repository.


.. include:: ../DEVELOPMENT.rst
