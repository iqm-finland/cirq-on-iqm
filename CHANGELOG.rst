=========
Changelog
=========

Version 1.0.0
=============

* Supports the Adonis and Valkmusa architectures.
* Extends the OpenQASM language with gates native to the IQM architectures.
* Loads quantum circuits from OpenQASM files.
* Decomposes gates into the native gate set.
* Optimizes the circuit by merging neighboring gates, and commuting z rotations towards the end of the circuit.

Version 1.1.0
=============

* Maps quantum circuits into qjobs-native gate sequences and executes them.
* Bump dependencies to Python 3.8, Cirq 0.9.1.

Version 1.2.0
=============

* Remove the qjobs dependency, the gate_mapper module, and the circuit execution functionality they provide.
* `qsim <https://quantumai.google/qsim>`_ can be used to simulate the circuit in addition to the
  standard Cirq simulators.
