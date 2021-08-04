User guide
==========

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
