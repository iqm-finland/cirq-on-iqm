Cirq on IQM
###########

:Release: |release|
:Date: |today|
:Source Code: `<https://github.com/iqm-finland/cirq-on-iqm>`_


`Google Cirq <https://quantumai.google/cirq>`_ adapter for `IQM's <https://www.meetiqm.com>`_ quantum architectures.


What is it good for?
====================

Currently Cirq on IQM can

* take an arbitrary quantum circuit created using Cirq or imported from an OpenQASM 2.0 file
* map the circuit into an equivalent one compatible with the chosen IQM quantum architecture
* optimize the circuit by commuting and merging gates
* simulate the circuit using one of Cirq's simulators
* run the circuit on an IQM quantum computer

Take a look at our :ref:`User guide` for an introduction on how to install and use Cirq on IQM.


Contents
========

.. toctree::
   :maxdepth: 2

   user_guide
   API
   license
   authors

.. toctree::
   :maxdepth: 1

   changelog


Indices
=======

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
