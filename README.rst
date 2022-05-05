========
httpexec
========

This is a web application for running arbitrary shell commands on the host
via HTTP. The intended use case for this is to make a Dockerized application
that only provides a CLI usable by other Docker containers.

**This application allows arbitrary remote execution. Beware of using this
for anything other than closed environments, like a like a local Docker
network.**

If using with Docker, it is best to `EXPOSE`_ the *httpexec* listening port
rather than `publishing`_ it so that access will be confined to other Docker
containers on the local network.


Minimum Requirements
====================

- Python 3.9+


Optional Requirements
=====================

- `pytest`_ (for running the test suite)
- `Sphinx`_ (for generating documentation)


Basic Setup
===========

Install for the current user:

.. code-block:: console

    $ python -m pip install . --user


Run the application:

.. code-block:: console

    $ python -m httpexec --help


Run the test suite:

.. code-block:: console
   
    $ pytest test/


Build documentation:

.. code-block:: console

    $ sphinx-build -b html doc doc/_build/html


.. _EXPOSE: https://docs.docker.com/engine/reference/builder/#expose
.. _publishing: https://docs.docker.com/config/containers/container-networking/
.. _pytest: http://pytest.org
.. _Sphinx: http://sphinx-doc.org
