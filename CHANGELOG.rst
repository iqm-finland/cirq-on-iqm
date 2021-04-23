=========
Changelog
=========


Version 0.2
===========

Features
--------

* Adonis native gate set updated, CZ-targeting decompositions added. :mr:`15`
* Circuits can be sent to be executed remotely on IQM hardware. :mr:`13`


Version 0.1
===========

Released 2021-04-21

Features
--------

* Supports the Adonis and Valkmusa architectures.
* Extends the OpenQASM language with gates native to the IQM architectures.
* Loads quantum circuits from OpenQASM files.
* Decomposes gates into the native gate set of the chosen architecture.
* Optimizes the circuit by merging neighboring gates, and commuting z rotations towards the end of the circuit.
* Circuits can be simulated using both the standard Cirq simulators and the
  `qsim <https://quantumai.google/qsim>`_ simulators.
