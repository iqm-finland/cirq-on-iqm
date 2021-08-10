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

Cirq on IQM provides descriptions of IQM's quantum architectures by providing various subclasses of :class:`.IQMDevice`.
The abstract class :class:`.IQMDevice` itself is a direct subclass of :code:`cirq.devices.Device` and implements general
functionality relevant to all IQM devices. Each device subclass describes the native gates and the connectivity of a particular architecture
and the relevant functionality. As an example, let us import the class :class:`.Adonis`, which describes IQM's
five-qubit architecture and view some of its properties contained in the class variables:

.. code-block:: python

    from cirq_iqm import Adonis

    print(Adonis.QUBIT_COUNT)
    print(Adonis.NATIVE_GATES)
    print(Adonis.CONNECTIVITY)


IQM devices use :code:`cirq.NamedQubits` to represent their qubits. The names of the qubits consist of a prefix
followed by a numeric index, so we have qubit names like :code:`QB1`, :code:`QB2`, etc. Note that we use 1-based
indexing. The qubit connectivity information is stored using the qubit indices only. You can get the list of the qubits
in a particular device by accessing the :code:`qubits` attribute of a corresponding :code:`IQMDevice` instance:

.. code-block:: python

    adonis = Adonis()
    print(adonis.qubits)


Constructing circuits
---------------------

There are three main ways (workflows) of using :code:`cirq.Circuit` with IQM devices

1. Create a Circuit instance associated with an IQMDevice, and use only the device qubits.
   Each :code:`cirq.Operation` is validated (i.e. checked that qubits are on the device, and properly connected) and
   decomposed as soon as it is appended to the circuit.
2. Create a Circuit instance with no associated device. Use arbitrary qubit names. There is no
   validation of the ops when appended. At any point the user can apply :meth:`.IQMDevice.decompose_circuit`
   to decompose the Circuit contents into the native set of the device, or :meth:`.IQMDevice.route_circuit`
   to route the circuit to the device connectivity.
3. Create a Circuit from an OpenQASM 2.0 program, qubits will have names like ``q_0`` with zero-based
   indexing. Proceed as in workflow 2.

Below we demonstrate examples of creating circuits in each of the three workflows.


Workflow 1
^^^^^^^^^^

Construct a circuit associated with the Adonis architecture. You have to use the qubits of the corresponding
device and respect the connectivity of the device when appending gates to the circuit.

.. code-block:: python

    import cirq

    adonis = Adonis()
    qb_1, qb_2 = adonis.qubits[:2]
    circuit_1 = cirq.Circuit(device=adonis)
    circuit_1.append(cirq.X(qb_1))
    circuit_1.append(cirq.H(qb_2))
    circuit_1.append(cirq.measure(qb_1, qb_2, key='mk'))


If you draw the circuit at this point, you will see that instead of the gates we have appended in the code it
contains their decompositions in terms of the native gate set of the Adonis device. This is because in this way of creating a circuit the gates are decomposed right away
when they are appended to the cirucit.


Workflow 2
^^^^^^^^^^

Construct a circuit with no associated device and use arbitrary qubit names:

.. code-block:: python

    import cirq

    qb_1, qb_2 = cirq.NamedQubit('Alice'), cirq.NamedQubit('Bob')
    circuit_2 = cirq.Circuit()
    circuit_2.append(cirq.X(qb_1))
    circuit_2.append(cirq.H(qb_2))
    circuit_2.append(cirq.measure(qb_1, qb_2, key='mk'))


After the circuit has been constructed, it can be decomposed and routed against a particular IQM device.
The method :meth:`.IQMDevice.decompose_circuit` accepts a :code:`cirq.Circuit` object as an argument and
returns the decomposed circuit containing only native gates for the corresponding device:

.. code-block:: python

    decomposed_circuit_2 = adonis.decompose_circuit(circuit_2)


The method :meth:`.IQMDevice.route_circuit` accepts a :code:`cirq.Circuit` object as an argument and returns
the circuit routed against the corresponding device:

.. code-block:: python

    routed_circuit_2 = adonis.route_circuit(circuit_2)

The routed circuit contains the qubits of the device instead of arbitrary named qubits we had originally.
By default :code:`route_circuit` returns only the routed circuit. However if you set its keyword argument
:code:`return_swap_network` to :code:`True`, it will return the full swap network object which contains the routed
circuit itself and the mapping between the used device qubits and the original ones.

Under the hood, the method :code:`route_circuit` leverages the router available in :code:`cirq.contrib.routing.router`.
Note, that this function works with circuits containing single- and two- qubit gates only. If you have gates involving
more than two qubits you need to decompose the circuit before routing. Since routing may add some swap gates to the
circuit you may need to decompose the circuit after routing once again if the swap gate is not a native gate for the
target device.


Workflow 3
^^^^^^^^^^

You can use your favorite tool to read an OpenQASM 2.0 program from a file or a string and convert it into a
:code:`cirq.Circuit` object. Once you have done this, you can follow the decomposition and routing steps described in
the previous workflow to prepare the circuit for execution against an IQM device.

You can also take a look at the function :func:`.extended_qasm_parser.circuit_from_qasm` which encompasses an
OpenQASM 2.0 parser shipped with Cirq on IQM and supports an extended set of gate names.


Running on a real quantum computer
----------------------------------

At this stage you can use your favorite Cirq simulator to simulate the circuits constructed above.
In this subsection we demonstrate how to run them against a real IQM quantum chip.

Cirq on IQM implements :class:`.iqm_remote.IQMSampler` as a subclass of :code:`cirq.work.Sampler` which should be used
for this purpose. You need to have access to an IQM server and obtain a settings file for the quantum hardware of
interest. Once these resources are in place, you can create an :code:`IQMSampler` instance and use its :code:`run`
method to send a circuit for execution and retrieve the results:

.. code-block:: python

    from cirq_iqm.iqm_remote import IQMSampler

    with open(iqm_settings_path, 'r') as f:
        sampler = IQMSampler(iqm_server_url, f.read(), adonis)
        result = sampler.run(circuit_1, repetitions=10)
        measurements = result.measurements['mk']
        print(measurements)


Note that the code snippet above assumes that you have variables called :code:`iqm_server_url` and
:code:`iqm_settings_path`.

Among other things, the settings file contains the definitions of the names of the qubits on the chip. We refer to
them as the physical names of the qubits, as opposed to the qubit names which appear in the circuit ('Alice' and 'Bob'
in our example). You need to specify how to make a correspondence between the qubits used in the circuit and the qubits
on the chip. The initializer of :code:`IQMSampler` accepts an optional argument called :code:`qubit_mapping` which
can be used to specify this correspondence. It is a dict mapping the circuit qubit names to physical names. Usually
the physical names of the qubits defined in the settings file coincide with the names of the qubits in an
:code:`IQMDevice` class, so if you have circuit which is already using the device qubits, then you don't need to specify
qubit mapping (as we did above for :code:`circuit_1` from the 1st workflow). However if the circuit is using other
qubits or the the physical names in the settings file do not coincide with the names in :code:`IQMDevice` for some
reason, you have to provide the qubit mapping:

.. code-block:: python

    qubit_mapping = {'Alice': 'QB1', 'Bob': 'QB2'}

    with open(iqm_settings_path, 'r') as f:
        sampler = IQMSampler(iqm_server_url, f.read(), adonis, qubit_mapping=qubit_mapping)
        result = sampler.run(decomposed_circuit_2, repetitions=10)
        measurements = result.measurements['mk']
        print(measurements)


More examples
-------------

More examples are available in the
`examples directory <https://github.com/iqm-finland/cirq-on-iqm/tree/main/examples>`_
of the Cirq on IQM github repository.


.. include:: ../DEVELOPMENT.rst