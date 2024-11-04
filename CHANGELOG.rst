=========
Changelog
=========

Version 15.2
============

* Drop support for Valkmusa architecture. `#140 <https://github.com/iqm-finland/qiskit-on-iqm/pull/140>`_

Version 15.1
============

* Bugfix: Accept unknown gates in the DQA.
  `#141 <https://github.com/iqm-finland/qiskit-on-iqm/pull/141>`_

Version 15.0
============

* Use dynamic quantum architecture for circuit decomposition and routing. `#139 <https://github.com/iqm-finland/cirq-on-iqm/pull/139>`_
* Require iqm-client >= 20.0. `#139 <https://github.com/iqm-finland/cirq-on-iqm/pull/139>`_
* Disable attestations on ``gh-action-pypi-publish`` to fix failing PyPI publishing. `#139 <https://github.com/iqm-finland/cirq-on-iqm/pull/139>`_

Version 14.6
============

* Bugfix COMP-1491: Fixed issue where `cirq_iqm` would ignore the MOVE gate validation options in CircuitCompilationOptions. `#136 <https://github.com/iqm-finland/cirq-on-iqm/pull/136>`_
* Removed `cirq_iqm` circuit validation when submitting to an IQM device because `iqm-client` already validates the circuit. 
* Added `isort` formatting to `tox -e format`.

Version 14.5
============

* Remove unnecessary build files when publishing documentation. `#138 <https://github.com/iqm-finland/iqm-client/pull/138>`_

Version 14.4
============

* Allow mid-circuit measurements. `#135 <https://github.com/iqm-finland/cirq-on-iqm/pull/135>`_
* Broken example code fixed. `#135 <https://github.com/iqm-finland/cirq-on-iqm/pull/135>`_

Version 14.3
============

* Improved operation validation to check if it is calibrated according to the metadata rather than assuming. `#133 <https://github.com/iqm-finland/cirq-on-iqm/pull/133>`_
* Added :class:`IQMMoveGate` class for Deneb architectures. `#133 <https://github.com/iqm-finland/cirq-on-iqm/pull/133>`_
* Updated :class:`IQMDevice` class to support devices with resonators. `#133 <https://github.com/iqm-finland/cirq-on-iqm/pull/133>`_
* Support for :class:`CircuitCompilationOptions` from ``iqm-client`` when submitting a circuit to an IQM device.
* Require iqm-client >= 18.0. `#133 <https://github.com/iqm-finland/cirq-on-iqm/pull/133>`_

Version 14.2
============

* Allow inspecting a run request before submitting it for execution. `#134 <https://github.com/iqm-finland/cirq-on-iqm/pull/134>`_
* Require iqm-client >= 17.8. `#134 <https://github.com/iqm-finland/cirq-on-iqm/pull/134>`_

Version 14.1
============

* Require iqm-client >= 17.6. `#132 <https://github.com/iqm-finland/cirq-on-iqm/pull/132>`_

Version 14.0
============

* Require iqm-client >= 17.1. `#128 <https://github.com/iqm-finland/cirq-on-iqm/pull/128>`_

Version 13.2
============

* Use GitHub Action as a Trusted Publisher to publish packages to PyPI. `#127 <https://github.com/iqm-finland/cirq-on-iqm/pull/127>`_

Version 13.1
============

* Remove multiversion documentation. `#125 <https://github.com/iqm-finland/cirq-on-iqm/pull/125>`_

Version 13.0
============

* Require iqm-client >= 16.0.
* Remove parameter ``circuit_duration_check`` from ``IQMSampler``.
* Add parameter ``max_circuit_duration_over_t2`` to ``IQMSampler``.

Version 12.2
============

* Require iqm-client >= 15.2. Bump dependencies and dev tools. `#121 <https://github.com/iqm-finland/cirq-on-iqm/pull/121>`_


Version 12.1
============

* Use latest version of ``sphinx-multiversion-contrib`` to fix documentation version sorting. `#120 <https://github.com/iqm-finland/cirq-on-iqm/pull/120>`_

Version 12.0
============

* Move ``cirq_iqm`` package to ``iqm`` namespace. `#119 <https://github.com/iqm-finland/cirq-on-iqm/pull/119>`_

Version 11.13
=============

* Add table of backend options and an example of submitting a batch of circuits to the user guide. `#117 <https://github.com/iqm-finland/cirq-on-iqm/pull/117>`_

Version 11.12
=============

* Return IQM Client metadata with results. `#109 <https://github.com/iqm-finland/cirq-on-iqm/pull/109>`_

Version 11.11
=============

* Submitted job is aborted if the user interrupts the program while it is waiting for results. `#114 <https://github.com/iqm-finland/cirq-on-iqm/pull/114>`_

Version 11.10
=============

* Make polling of circuit results configurable. `#113 <https://github.com/iqm-finland/cirq-on-iqm/pull/113>`_

Version 11.9
============

* Add parameter ``heralding`` to ``IQMSampler``. `#112 <https://github.com/iqm-finland/cirq-on-iqm/pull/112>`_
* Upgrade to IQMClient version 12.5 `#112 <https://github.com/iqm-finland/cirq-on-iqm/pull/112>`_

Version 11.8
============

* Upgrade to IQMClient version 12.4 `#111 <https://github.com/iqm-finland/cirq-on-iqm/pull/111>`_
* Add parameter ``circuit_duration_check`` to ``IQMSampler`` allowing to control server-side maximum circuit duration check `#111 <https://github.com/iqm-finland/cirq-on-iqm/pull/111>`_

Version 11.7
============

* Generate license information for dependencies on every release `#108 <https://github.com/iqm-finland/cirq-on-iqm/pull/108>`_

Version 11.6
============

* Upgrade to IQMClient version 12.2 `#107 <https://github.com/iqm-finland/cirq-on-iqm/pull/107>`_

Version 11.5
============

* Upgrade to IQMClient version 12.0 `#106 <https://github.com/iqm-finland/cirq-on-iqm/pull/106>`_

Version 11.4
============

* "Pin down" supported Python versions to 3.9 and 3.10. `#102 <https://github.com/iqm-finland/cirq-on-iqm/pull/102>`_
* Configure Tox to skip missing versions of Python interpreters when running tests. `#102 <https://github.com/iqm-finland/cirq-on-iqm/pull/102>`_
* Move project metadata and configuration to ``pyproject.toml``. `#102 <https://github.com/iqm-finland/cirq-on-iqm/pull/102>`_

Version 11.3
============

* Provide version information to IQMClient. `#104 <https://github.com/iqm-finland/cirq-on-iqm/pull/104>`_

Version 11.2
============

* Build and publish docs for older versions fixes. `#103 <https://github.com/iqm-finland/cirq-on-iqm/pull/103>`_

Version 11.1
============

* Build and publish docs for older versions. `#101 <https://github.com/iqm-finland/cirq-on-iqm/pull/101>`_

Version 11.0
============

* Use new opaque UUID for ``calibration_set_id``. `#98 <https://github.com/iqm-finland/cirq-on-iqm/pull/98>`_

Version 10.1
============

* Add :meth:`.IQMSampler.run_iqm_batch` for running multiple circuits in a batch. `#100 <https://github.com/iqm-finland/cirq-on-iqm/pull/100>`_

Version 10.0
============

* Replace routing function from cirq.contrib with newly added routing functionality in cirq 1.1. `#97 <https://github.com/iqm-finland/cirq-on-iqm/pull/97>`_

Version 9.0
===========

* User guide updated.

Bugfixes
--------

* :meth:`.IQMDevice.route_circuit` bugfix: ``initial_mapping`` must be reversed to match the
  :mod:`cirq.contrib.routing.greedy` convention.

Version 8.2
===========

* Upgrade to IQMClient version 10.0. `#95 <https://github.com/iqm-finland/cirq-on-iqm/pull/95>`_

Version 8.1
===========

* ``IQMDevice.route_circuit`` accepts ``initial mapping`` `#93 <https://github.com/iqm-finland/cirq-on-iqm/pull/93>`_
* ``IQMSampler`` no longer accepts ``qubit_mapping`` `#93 <https://github.com/iqm-finland/cirq-on-iqm/pull/93>`_

Version 8.0
===========

* Implement metadata for IQM devices. `#92 <https://github.com/iqm-finland/cirq-on-iqm/pull/92>`_

Version 7.8
===========

* Bump ``iqm-client`` dependency. `#91 <https://github.com/iqm-finland/cirq-on-iqm/pull/91>`_

Version 7.7
===========

* Enable mypy support. `#88 <https://github.com/iqm-finland/cirq-on-iqm/pull/88>`_

Version 7.6
===========

* Upgrade to IQMClient version 8.0.
* Remove ``settings`` parameter from ``IQMSampler``.

Version 7.5
===========

* Upgrade to IQMClient version 7.0.

Version 7.4
===========

* ``cortex-cli`` is now the preferred way of authentication.

Version 7.3
===========

* Use cirq 1.0. `#82 <https://github.com/iqm-finland/cirq-on-iqm/pull/82>`_

Version 7.2
===========

* Update ``IQMClient`` instantiations with the changes in iqm-client 6.1. `#80 <https://github.com/iqm-finland/cirq-on-iqm/pull/80>`_
* ``IQMSampler`` now accepts an optional ``calibration_set_id``. `#80 <https://github.com/iqm-finland/cirq-on-iqm/pull/80>`_
* Update documentation regarding the use of Cortex CLI. `#80 <https://github.com/iqm-finland/cirq-on-iqm/pull/80>`_

Version 7.1
===========

* Support iqm-client 6.0. `#79 <https://github.com/iqm-finland/cirq-on-iqm/pull/79>`_

Version 7.0
===========

* Update ``IQMClient`` instantiations with the changes in iqm-client 5.0 `#75 <https://github.com/iqm-finland/cirq-on-iqm/pull/75>`_
* ``IQMSampler`` now accepts ``settings`` as dict instead of raw string file content `#75 <https://github.com/iqm-finland/cirq-on-iqm/pull/75>`_

Version 6.1
===========

* Support iqm-client 4.3. `#78 <https://github.com/iqm-finland/cirq-on-iqm/pull/78>`_

Version 6.0
===========

* Allow running sweeps in ``IQMSampler.run_sweep`` . `#76 <https://github.com/iqm-finland/cirq-on-iqm/pull/76>`_

Version 5.0
===========

* Make ``settings`` an optional parameter for ``IQMSampler``. Optional ``settings`` is now after non-optional ``device`` in arguments. `#73 <https://github.com/iqm-finland/cirq-on-iqm/pull/73>`_
* Requires iqm-client 3.3

Version 4.1
===========

* Add support for 20-qubit Apollo architecture. `#72 <https://github.com/iqm-finland/cirq-on-iqm/pull/72>`_

Version 4.0
===========

* Update user authentication to use access token. `#71 <https://github.com/iqm-finland/cirq-on-iqm/pull/71>`_
* Upgrade IQMClient to version >= 2.0 `#71 <https://github.com/iqm-finland/cirq-on-iqm/pull/71>`_

Version 3.6
===========

* Update optimizers, tests and relevant Jupyter examples to fix deprecation warnings in preparation for cirq 0.15 and cirq 1.0. `#70 <https://github.com/iqm-finland/cirq-on-iqm/pull/70>`_

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
