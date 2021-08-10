How to develop and contribute
-----------------------------

Cirq on IQM is an open source Python project.
You can contribute by creating GitHub issues to report bugs or request new features,
or by opening a pull request to submit your own improvements to the codebase.

To start developing the project, clone the
`GitHub repository <https://github.com/iqm-finland/cirq-on-iqm>`_
and install it in editable mode with all the extras:

.. code-block:: bash

   $ git clone git@github.com:iqm-finland/cirq-on-iqm.git
   $ cd cirq-on-iqm
   $ pip install -e ".[dev,docs,testing]"


Build and view the docs:

.. code-block:: bash

   $ tox -e docs
   $ firefox build/sphinx/html/index.html


Run the tests:

.. code-block:: bash

   $ tox
