|CI badge| |Release badge| |Black badge|

.. |CI badge| image:: https://github.com/iqm-finland/cirq-on-iqm/actions/workflows/ci.yml/badge.svg
.. |Release badge| image:: https://img.shields.io/github/release/iqm-finland/cirq-on-iqm.svg
.. |Black badge| image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black

Cirq on IQM
###########

`Google Cirq <https://quantumai.google/cirq>`_ adapter for `IQM's <https://www.meetiqm.com>`_ quantum architectures.


What is it good for?
====================

Currently Cirq on IQM can

* take an arbitrary quantum circuit created using Cirq or imported from an OpenQASM 2.0 file
* map the circuit into an equivalent one compatible with the chosen IQM quantum architecture
* optimize the circuit by commuting and merging gates
* simulate the circuit using one of Cirq's simulators
* run the circuit on an IQM quantum computer


Installation
============

The recommended way is to install the distribution package ``cirq-iqm`` directly from the
Python Package Index (PyPI):

.. code-block:: bash

   $ pip install cirq-iqm


Documentation
=============

The documentation of the latest Cirq on IQM release is available
`here <https://iqm-finland.github.io/cirq-on-iqm/index.html>`_.

Jump to our `User guide <https://iqm-finland.github.io/cirq-on-iqm/user_guide.html>`_
for a quick introduction on how to use Cirq on IQM.

Take a look at the `Jupyter notebook <https://jupyter.org/>`_ with examples: ``examples/usage.ipynb``.

You can build documentation for any older version locally by cloning the Git repository, checking out the 
corresponding tag, and running the docs builder. For example, to build the documentation for version ``12.2``:

.. code-block:: bash

    $ git clone git@github.com:iqm-finland/cirq-on-iqm.git
    $ cd cirq-on-iqm
    $ git checkout 12.2
    $ tox run -e docs

``tox run -e docs`` will build the documentation at ``./build/sphinx/html``. This command requires the ``tox,``, ``sphinx`` and 
``sphinx-book-theme`` Python packages (see the ``docs`` optional dependency in ``pyproject.toml``); 
you can install the necessary packages with ``pip install -e ".[dev,docs]"``


Copyright
=========

Cirq on IQM is free software, released under the Apache License, version 2.0.

Copyright 2020–2024 Cirq on IQM developers.
