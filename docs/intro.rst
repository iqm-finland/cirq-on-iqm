Cirq on IQM
===========

`Google Cirq <https://github.com/quantumlib/Cirq>`_ adapter for IQM's quantum architectures.


What is it good for?
--------------------

Currently Cirq on IQM can

* take an arbitrary quantum circuit created in Cirq or load from an OpenQASM 2.0 file
* map the circuit into an equivalent one compatible with the chosen IQM quantum architecture
* optimize the circuit by commuting and merging gates
* simulate the circuit using one of Cirq's simulators
* run the circuit on an IQM quantum computer