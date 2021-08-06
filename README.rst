|CI badge| |Release badge|

.. |CI badge| image:: https://github.com/iqm-finland/cirq-on-iqm/actions/workflows/ci.yml/badge.svg
.. |Release badge| image:: https://img.shields.io/github/release/iqm-finland/cirq-on-iqm.svg


Cirq on IQM
===========

`Google Cirq <https://github.com/quantumlib/Cirq>`_ adapter for IQM's quantum architectures.


What is it good for?
--------------------

Currently Cirq on IQM can

* take an arbitrary quantum circuit created using Cirq or imported from an OpenQASM 2.0 file
* map the circuit into an equivalent one compatible with the chosen IQM quantum architecture
* optimize the circuit by commuting and merging gates
* simulate the circuit using one of Cirq's simulators
* run the circuit on an IQM quantum computer


Documentation
=============

Cirq on IQM documentation is available `here <https://iqm-finland.github.io/cirq-on-iqm/index.html>`_.

Jump to our `Getting started with Cirq on IQM <https://iqm-finland.github.io/cirq-on-iqm/getting_started.html>`_
guide for a quick introduction on how to install and use Cirq on IQM.

See the `Jupyter Notebook <https://jupyter.org/>`_ with examples: ``examples/usage.ipynb``.


Copyright
=========

Cirq on IQM is free software, released under the Apache License, version 2.0.

Copyright 2020–2021 Cirq on IQM developers.
