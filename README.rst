========
httpexec
========

|badge|

This is a web application for running arbitrary shell commands on its host
via HTTP. The intended use case is to make a CLI application inside a Docker
container usable from other containers.

**This application allows arbitrary remote execution. Beware of using this
for anything other than closed environments, like a like a local Docker
network.**

When using with Docker, it is best to `EXPOSE`_ the *httpexec* listening port
rather than `publishing`_ it so that access will be confined to other
containers on the local Docker network.


Minimum Requirements
====================

- Python 3.9+



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


.. _GitHub Actions: https://github.com/mdklatt/httpexec/actions/workflows/tests.yml
.. |badge| image:: https://github.com/mdklatt/httpexec/actions/workflows/tests.yml/badge.svg
    :alt: GitHub Actions test status
    :target: `GitHub Actions`_
.. _EXPOSE: https://docs.docker.com/engine/reference/builder/#expose
.. _publishing: https://docs.docker.com/config/containers/container-networking/
.. _pytest: http://pytest.org
.. _Sphinx: http://sphinx-doc.org
