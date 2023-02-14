========
httpexec
========

|python3.9|
|python3.10|
|release|
|license|
|tests|

This is a web application for running arbitrary shell commands on its host
via HTTP. The intended use case is to make a CLI application inside a Docker
container usable from other containers.

**This application allows arbitrary remote execution. Beware of using this
for anything other than closed environments, like a like a local Docker
network.**

When using with Docker, it is best to `EXPOSE`_ the *httpexec* listening port
rather than `publishing`_ it so that access will be confined to other
containers on the local Docker network.


---
API
---

Requests
--------

``POST`` requests as ``application/json`` to ``http://<host>[:<port>]/<command>``.

The ``command`` must be within the ``HTTPEXEC_EXEC_ROOT`` path.

.. code-block:: json

    {
      "args": [],
      "stdin": "",
      "binary": {
        "stdin": null,
        "stdout": null,
        "stderr": null
      }
    }


Responses
---------

If the command was executed, a ``200`` (``OK``) status is returned along with
a JSON response. This does not mean that the command was successful; check the
``return`` value in the response to determine the exit status returned by the
command.

If the requested command is not found within ``HTTPEXEC_EXEC_ROOT``, a ``403``
(``FORBIDDEN``) status is returned.

.. code-block:: json

    {
      "return": 0,
      "stdout": "",
      "stdouerr": ""
    }



-----------
Basic Setup
-----------

Installation
-------------

Install the application.

.. code-block:: console

    $ python -m venv .venv
    $ source .venv/bin/activate
    (.venv) $ python -m pip install .


Install an `ASGI server`_, *e.g.* `Hypercorn`_.

.. code-block:: console

    (.venv) $ python -m pip install hypercorn


Running
-------

Run the ASGI server:

.. code-block:: console
   
    (.venv) $ python -m hypercorn --error-logfile - --access-logfile - --bind 127.0.0.1:8000 httpexec.asgi:app


Configuration
-------------

**TODO**

-----------
Development
-----------

Set up a development environment:

.. code-block:: console

    $ make dev

Run tests
---------

Run all tests:

.. code-block:: console

    $ make test


Build documentation
-------------------

**TODO**


.. |python3.9| image:: https://img.shields.io/static/v1?label=python&message=3.9&color=informational
    :alt: Python 3.9
.. |python3.10| image:: https://img.shields.io/static/v1?label=python&message=3.10&color=informational
    :alt: Python 3.10
.. |release| image:: https://img.shields.io/github/v/release/mdklatt/httpexec?sort=semver
    :alt: GitHub release (latest SemVer)
.. |license| image:: https://img.shields.io/github/license/mdklatt/httpexec
    :alt: MIT License
    :target: `MIT License`_
.. |tests| image:: https://github.com/mdklatt/httpexec/actions/workflows/tests.yml/badge.svg
    :alt: CI Tests
    :target: `GitHub Actions`_

.. _MIT License: https://choosealicense.com/licenses/mit
.. _GitHub Actions: https://github.com/mdklatt/httpexec/actions/workflows/tests.yml
.. _EXPOSE: https://docs.docker.com/engine/reference/builder/#expose
.. _publishing: https://docs.docker.com/config/containers/container-networking/
.. _ASGI server: https://asgi.readthedocs.io/en/latest/implementations.html
.. _Hypercorn: https://pgjones.gitlab.io/hypercorn
