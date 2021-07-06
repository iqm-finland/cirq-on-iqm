=========
Changelog
=========


Version 0.7
===========

Bugfixes
--------

* Off-by-one error fixed in :meth:`IQMDevice.map_circuit`. :mr:`29`


Version 0.6
===========

Features
--------

* Project setup updated. :mr:`22`

  * ``pyproject.toml`` added.
  * ``PyScaffold`` dependency removed.
  * Sphinx bumped to version 4.0.2.
  * API docs generated using recursive ``sphinx.ext.autosummary``.
  * ``tox`` scripts for building docs, dist packages.


Version 0.5
===========

Features
--------

* Gate decomposition and circuit optimization procedure simplified. :mr:`21`
* Cirq dependency bumped to 0.11. :mr:`23`

NOTE: Before installing this version, please manually uninstall Cirq 0.10. See Cirq 0.11
release notes for more details: https://github.com/quantumlib/Cirq/releases/tag/v0.11.0


Version 0.4
===========

Features
--------

* Convert data to IQM internal format when running requests. :mr:`20`


Version 0.3
===========

Features
--------

* Settings file support. :mr:`17`


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
