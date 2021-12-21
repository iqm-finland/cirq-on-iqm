=========
Changelog
=========

Version 3.5
===========

* Configure automatic tagging and releasing. `#64 <https://github.com/iqm-finland/cirq-on-iqm/pull/64>`_

Version 3.4
===========

* Add HTTP Basic auth. `#62 <https://github.com/iqm-finland/cirq-on-iqm/pull/62>`_

Version 3.3 (2021-11-15)
========================

* Bump the ``iqm-client`` dependency to 1.4, remove the strict pinning.
  Bump ``build`` to 0.7.0.
  `#58 <https://github.com/iqm-finland/cirq-on-iqm/pull/58>`_


Version 3.2 (2021-11-02)
========================

* Add functionality for routing circuits with multi-qubit measurements. `#56 <https://github.com/iqm-finland/cirq-on-iqm/pull/56>`_


Version 3.1 (2021-10-19)
========================

* Update the cirq dependency to version 0.13
* Remove unused argument from Circuit


Version 3.0 (2021-10-12)
========================

* Raise an error if MeasurementGate has an ``invert_mask``. `#53 <https://github.com/iqm-finland/cirq-on-iqm/pull/53>`_


Version 2.1 (2021-09-21)
=========================

Features
--------

* ``circuit_from_qasm`` imports OpenQASM 2.0 gates ``U`` and ``u3`` of the form ``U(a, b, -b)``
  as ``cirq.PhasedXPowGate``. `#46 <https://github.com/iqm-finland/cirq-on-iqm/pull/46>`_
* Add an equals method to IQMDevice such that all instances of the same device architecture
  are considered equivalent. `#50 <https://github.com/iqm-finland/cirq-on-iqm/pull/50>`_


Version 2.0 (2021-09-17)
========================

* The codebase is reorganized.
  `#46 <https://github.com/iqm-finland/cirq-on-iqm/pull/46>`_
* Redundant functionality for final decompositions is removed.
  `#46 <https://github.com/iqm-finland/cirq-on-iqm/pull/46>`_
* Support for obsolete IQM OpenQASM extension is removed.
  `#45 <https://github.com/iqm-finland/cirq-on-iqm/pull/45>`_


Version 1.2 (2021-09-03)
========================

Features
--------

* Move IQM client to a `separate library <https://pypi.org/project/iqm-client/>`_
* Adonis native gate set updated, Rz is not native.
  `#41 <https://github.com/iqm-finland/cirq-on-iqm/pull/41>`_

Bugfixes
--------

* DropRZMeasurements sometimes did not remove z rotations it should have.
  `#41 <https://github.com/iqm-finland/cirq-on-iqm/pull/41>`_


Version 1.1 (2021-08-13)
========================

* The version of ``requests`` dependency is relaxed.
* Minor aesthetic changes in the documentation.


Version 1.0 (2021-08-11)
========================

Features
--------

* ``IQMDevice`` updated. `#35 <https://github.com/iqm-finland/cirq-on-iqm/pull/35>`_

  * ``IQMDevice.map_circuit`` removed.
  * ``IQMDevice.decompose_circuit`` and ``IQMDevice.route_circuit`` methods added.
  * ``IQMDevice.simplify_circuit`` now checks if it has hit a fixed point after each iteration.
  * ``IQMSampler`` checks that the circuit respects the device connectivity.

* Device qubit handling is simplified. `#34 <https://github.com/iqm-finland/cirq-on-iqm/pull/34>`_

  * ``IQMSampler`` can generate a trivial qubit mapping automatically.
  * The class ``IQMQubit`` was removed.

* Documentation updated. `#36 <https://github.com/iqm-finland/cirq-on-iqm/pull/36>`_

  * The documentation now contains a concise user guide.
  * Documentation published online.

Bugfixes
--------

* All the demos work again. `#35 <https://github.com/iqm-finland/cirq-on-iqm/pull/35>`_
* ``DropRZBeforeMeasurement`` had a bug where it sometimes incorrectly eliminated a z rotation
  followed by a multiqubit gate. `#35 <https://github.com/iqm-finland/cirq-on-iqm/pull/35>`_


Version 0.7 (2021-07-07)
========================

Bugfixes
--------

* Off-by-one error fixed in `IQMDevice.map_circuit <https://github.com/iqm-finland/cirq-on-iqm/blob/a2d09dab583434c89f569e711ac35085ec371342/src/cirq_iqm/iqm_device.py#L120>`_. `#29 <https://github.com/iqm-finland/cirq-on-iqm/pull/29>`_


Version 0.6 (2021-07-02)
========================

Features
--------

* Project setup updated. `#22 <https://github.com/iqm-finland/cirq-on-iqm/pull/22>`_

  * ``pyproject.toml`` added.
  * ``PyScaffold`` dependency removed.
  * Sphinx bumped to version 4.0.2.
  * API docs generated using recursive ``sphinx.ext.autosummary``.
  * ``tox`` scripts for building docs, dist packages.


Version 0.5 (2021-06-24)
========================

Features
--------

* Gate decomposition and circuit optimization procedure simplified. `#21 <https://github.com/iqm-finland/cirq-on-iqm/pull/21>`_
* Cirq dependency bumped to 0.11. `#23 <https://github.com/iqm-finland/cirq-on-iqm/pull/23>`_

NOTE: Before installing this version, please manually uninstall Cirq 0.10. See Cirq 0.11
release notes for more details: https://github.com/quantumlib/Cirq/releases/tag/v0.11.0


Version 0.4 (2021-06-23)
========================

Features
--------

* Convert data to IQM internal format when running requests. `#20 <https://github.com/iqm-finland/cirq-on-iqm/pull/20>`_


Version 0.3 (2021-06-09)
========================

Features
--------

* Settings file support. `#17 <https://github.com/iqm-finland/cirq-on-iqm/pull/17>`_


Version 0.2 (2021-04-23)
========================

Features
--------

* Adonis native gate set updated, CZ-targeting decompositions added. `#15 <https://github.com/iqm-finland/cirq-on-iqm/pull/15>`_
* Circuits can be sent to be executed remotely on IQM hardware. `#13 <https://github.com/iqm-finland/cirq-on-iqm/pull/13>`_


Version 0.1 (2021-04-22)
========================

Features
--------

* Supports the Adonis and Valkmusa architectures.
* Extends the OpenQASM language with gates native to the IQM architectures.
* Loads quantum circuits from OpenQASM files.
* Decomposes gates into the native gate set of the chosen architecture.
* Optimizes the circuit by merging neighboring gates, and commuting z rotations towards the end of the circuit.
* Circuits can be simulated using both the standard Cirq simulators and the
  `qsim <https://quantumai.google/qsim>`_ simulators.
