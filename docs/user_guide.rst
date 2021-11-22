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

Cirq on IQM provides descriptions of IQM's quantum architectures as subclasses of :class:`.IQMDevice`.
The abstract class :class:`.IQMDevice` itself is a subclass of :class:`cirq.devices.Device` and implements general
functionality relevant to all IQM devices. Each device subclass describes the native gates and the connectivity of a particular architecture
and the relevant functionality. As an example, let us import the class :class:`.Adonis`, which describes IQM's
five-qubit architecture and view some of its properties contained in the class variables:

.. code-block:: python

    from cirq_iqm import Adonis

    print(Adonis.QUBIT_COUNT)
    print(Adonis.NATIVE_GATES)
    print(Adonis.CONNECTIVITY)


IQM devices use :class:`cirq.NamedQubit` to represent their qubits. The names of the qubits consist of a prefix
followed by a numeric index, so we have qubit names like ``QB1``, ``QB2``, etc. Note that we use 1-based
indexing. The qubit connectivity information is stored using the qubit indices only. You can get the list of the qubits
in a particular device by accessing the ``qubits`` attribute of a corresponding :class:`.IQMDevice` instance:

.. code-block:: python

    adonis = Adonis()
    print(adonis.qubits)


Constructing circuits
---------------------

There are three main workflows of using :class:`cirq.Circuit` instances with IQM devices:

1. Create a ``Circuit`` instance associated with an ``IQMDevice``, and use only the device qubits.
   Each :class:`cirq.Operation` is validated (i.e. checked that qubits are on the device, and properly connected) and
   decomposed into native operations as soon as it is appended to the circuit.
2. Create a ``Circuit`` instance with no associated device, use arbitrary qubit names and types. There is no
   validation of the operations when appended. At any point the user can apply :meth:`.IQMDevice.decompose_circuit`
   to decompose the circuit contents into the native operation set of the device, or :meth:`.IQMDevice.route_circuit`
   to route the circuit to the device connectivity and device qubits.
3. Create a ``Circuit`` from an OpenQASM 2.0 program. The qubit names are determined by the OpenQASM ``qreg`` names,
   appended with zero-based indices. Proceed as in workflow 2.

Below we demonstrate examples of creating circuits in each of the three workflows.


Workflow 1
^^^^^^^^^^

Construct a circuit associated with the Adonis architecture. You have to use the qubits of the corresponding
device and respect the connectivity of the device when appending gates to the circuit.

.. code-block:: python

    import cirq
    from cirq_iqm import Adonis

    adonis = Adonis()
    q1, q2, q3 = adonis.qubits[:3]
    circuit_1 = cirq.Circuit(device=adonis)
    circuit_1.append(cirq.X(q1))
    circuit_1.append(cirq.H(q3))
    circuit_1.append(cirq.CNOT(q1, q3))
    circuit_1.append(cirq.measure(q1, q3, key='m'))
    print(circuit_1)

If you print the circuit at this point, you will see that instead of the gates we have appended, it
contains their decompositions in terms of the native gate set of the ``Adonis`` device.
This is because in this way of creating a circuit the gates are decomposed right away
when they are appended to the circuit::

   QB1: ───X────────────────────@───────────M('m')───
                                │           │
   QB3: ───Y^0.5───X───Y^-0.5───@───Y^0.5───M────────

.. _workflow_2:

Workflow 2
^^^^^^^^^^

Construct a circuit with no associated device and use arbitrary qubits:

.. code-block:: python

    import cirq
    from cirq_iqm import Adonis

    q1, q2 = cirq.NamedQubit('Alice'), cirq.NamedQubit('Bob')
    circuit_2 = cirq.Circuit()
    circuit_2.append(cirq.X(q1))
    circuit_2.append(cirq.H(q2))
    circuit_2.append(cirq.CNOT(q1, q2))
    circuit_2.append(cirq.measure(q1, q2, key='m'))
    print(circuit_2)

This will result in the circuit
::

   Alice: ───X───@───M('m')───
                 │   │
   Bob: ─────H───X───M────────

After the circuit has been constructed, it can be decomposed and routed against a particular ``IQMDevice``.
The method :meth:`.IQMDevice.decompose_circuit` accepts a :class:`cirq.Circuit` object as an argument and
returns the decomposed circuit containing only native gates for the corresponding device:

.. code-block:: python

    decomposed_circuit_2 = adonis.decompose_circuit(circuit_2)


The method :meth:`.IQMDevice.route_circuit` accepts a :class:`cirq.Circuit` object as an argument,
and returns the circuit routed against the device, acting on the device qubits instead of the
arbitrary qubits we had originally.

.. code-block:: python

    routed_circuit_2 = adonis.route_circuit(decomposed_circuit_2)
    print(routed_circuit_2)


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

    simplified_circuit_2 = simplify_circuit(routed_circuit_2)
    print(simplified_circuit_2)


::

    QB3: ───PhX(1)───@───────────────────M('m')───
                     │                   │
    QB5: ────────────@───PhX(-0.5)^0.5───M────────


.. note::

    The funtion :func:`.simplify_circuit` is not associated with any IQM device, so its result may contain non-native
    gates for a particular device. In the example above we don't have them, however it is generally a good idea to run
    decomposition once again after the simplification.


Workflow 3
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
        circuit_3 = cirq_iqm.circuit_from_qasm(f.read())
    print(circuit_3)

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
to execute quantum circuits. You need to have access to an IQM server and have a settings file for
the quantum hardware of interest. Once these resources are in place, you can create an
:class:`.IQMSampler` instance and use its :meth:`~.IQMSampler.run` method to send a circuit for execution
and retrieve the results:

.. code-block:: python

   from cirq_iqm.iqm_sampler import IQMSampler

   with open(iqm_settings_path, 'r') as f:
       sampler = IQMSampler(iqm_server_url, f.read(), adonis)

   result = sampler.run(circuit_1, repetitions=10)
   print(result.measurements['m'])


Note that the code snippet above assumes that you have set the variables ``iqm_server_url`` and
``iqm_settings_path``. If the IQM server you are connecting to requires authentication, you will also have to set
the IQM_SERVER_USERNAME and IQM_SERVER_API_KEY environment variables.

When executing a circuit that uses something other than the device qubits, you need to either route it first
as explained in :ref:`workflow 2 <workflow_2>` above,
or provide the mapping from the *logical* qubits in the circuit to the *physical* qubits on the device yourself.
The initializer of :class:`.IQMSampler` accepts an optional argument called ``qubit_mapping`` which
can be used to specify this correspondence.

.. code-block:: python

    qubit_mapping = {'Alice': 'QB1', 'Bob': 'QB3'}

    with open(iqm_settings_path, 'r') as f:
        sampler = IQMSampler(iqm_server_url, f.read(), adonis, qubit_mapping=qubit_mapping)

    result = sampler.run(decomposed_circuit_2, repetitions=10)
    print(result.measurements['m'])

If you have a circuit which already uses the device qubits, you don't need to specify
the qubit mapping (as we did above for ``circuit_1``).


More examples
-------------

More examples are available in the
`examples directory <https://github.com/iqm-finland/cirq-on-iqm/tree/main/examples>`_
of the Cirq on IQM repository.


.. include:: ../DEVELOPMENT.rst
