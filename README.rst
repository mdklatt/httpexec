########
httpexec
########

|python3.9|
|python3.10|
|python3.11|
|license|
|release|
|pypi|
|tests|

*httpexec* is an `Asynchronous Server Gateway Interface`_ (ASGI) application
that allows remote clients to execute CLI commands on the local host via a
REST API. An `ASGI-capable server`_ is also required.

**There are critical security considerations when using this application.** See
the `Security`_ section.


.. image:: docs/httpexec.png
  :alt: httpexec System Architecture


========
REST API
========

See the project's `OpenAPI`_ spec file (``openapi.yaml``) for more information.


Requests
--------

The application accepts ``POST`` requests as ``application/json`` to the
``/<command>`` endpoint of its bound address. The request defines the
arguments, input and output streams, and environment variables that will be
used to for executing the command.

This sample request sent to endpoint ``/app`` will execute ``app -o option``
on the local host with the string ``input`` piped to ``STDIN``. The contents of
``STDOUT`` will be captured and returned to the client using Base64 encoding.
The variable ``FOO=BAR`` will be added to the execution environment. The
contents of ``STDERR`` will not be captured.

.. code-block:: json

    {
      "args": ["-o", "option"],
      "stdin": {"content": "input"},
      "stdout": {"capture": true, "encode": "base64"},
      "environment": {"FOO": "BAR"}
    }

Responses
---------

If the command was executed, a ``200`` (``OK``) status is returned along with
an  ``application/json`` response. This does **not** mean the command itself
was successful; the ``return`` value in the response is the exit status
returned by the command.

If the requested command is not found, a ``404`` (``Not Found``) status is
returned. If the command could not be executed due to an unexpected error, a
``500`` (``Internal Server Error``) status is returned.


If the sample request from above was executed, a response like this will be
returned. The command returned an exit status of ``0``, the output to
``STDERR`` was not captured, and the output to ``STDOUT`` is encoded binary
data.

.. code-block:: json

    {
      "return": 0,
      "stderr": null,
      "stdout": {"content": "YmluYXJ5IGRhdGE=", "encode": "base64"}
    }


Binary Data
-----------

JSON cannot handle arbitrary binary data. Any binary input to ``STDOUT`` or
output from ``STDERR`` or ``STDOUT`` must be encoded as text strings. The
client must *encode* the content of ``STDIN`` in the request and *decode* the
contents of ``STDERR`` and ``STDOUT`` from the response. *httpexec* will
*decode* the content of ``STDIN`` from the request and *encode* the contents of
``STDERR`` and ``STDOUT`` in the response. Thus, encoding is transparent to the
target command.

*httpexec* currently supports two encoding schemes, `base64`_ and `base85`_. If
the target command implements its own text-safe encoding for binary data, use
``"encode": null`` (or omit it) in the request to make this transparent to
*httpexec*.


===========
Basic Setup
===========

Installation
-------------

Install the application, its runtime dependencies, and the `Hypercorn`_ web
server:

.. code-block:: console

    $ python -m pip install httpexec "hypercorn>=0.14.3,<1"

Pinned Dependencies
+++++++++++++++++++

Production applications should pin their dependencies to exact versions to
avoid unexpected breaking changes. The downside of this is that it makes it
more difficult to receive critical updates. This application relies on
`Semantic Versioning`_ for its own dependencies to minimize breaking changes
while allowing for routine updates (see *pyproject.toml*). Users should use
their packaage manager to pin this package and its dependencies to exact
versions in a production environment.


Configuration
-------------

User-configurable options can be set using a `TOML`_ config file or an
environment variable. Environment variable names must be prefixed with
``HTTPEXEC_``, *e.g.* ``HTTPEXEC_EXEC_ROOT`` sets ``EXEC_ROOT``. Environment
variables have precedence over the config file.


``EXEC_ROOT``
  For security, *httpexec* will not execute any command outside of this
  directory. **This must be set explicitly by the user.**

``FOLLOW_LINKS``
  This is a boolean that controls whether or not *httpexec* will follow a
  symbolic link to a path outside of ``EXEC_ROOT``. If true, the link itself
  must still be within ``EXEC_ROOT``. For an environment variable use ``1``
  for true and ``0`` for false. For security, the default value is false.

``LOGGING_LEVEL``
  The application uses standard `Python logging`_, and this sets the logging
  level. Messages of a lower severity will not be be logged. The default level
  is ``WARNING``.

``CONFIG_PATH``
  This is the path to the optional config file.
  **This can only set by environment variable.**


Execution
---------

Start the web server, and *httpexec* will be available at the bound address.

.. code-block:: console
   
    $ python -m hypercorn --error-logfile - --access-logfile - --bind 127.0.0.1:8000 httpexec.asgi:app

The *httpexec* execution environment is set by the web server, which will also
impact the execution environment of the commands being executed by *httpexec*.
For example, this will determine whether or not *httpexec* has permission to
run a target command, and the environment variables that are available to the
command. See the web server's documentation.


========
Security
========

**Allowing arbitrary remote execution is a significant security risk.**

Do not use *httpexec* without understanding all of the security implications.
This application was developed for a specific use case: Allowing a CLI command
in one Docker container to be executed by another Docker container. Docker
makes it easier to provide multiple layers of security, but this is also
possible without Docker. **The following advice is not authoritative.**
**USE AT YOUR RISK.**


Network Isolation
-----------------

Access to the address *httpexec* is bound to must be **strictly controlled**.
Under no circumstances should this be globally visible to the outside world.
By default, a Docker container is only accessible to other Docker containers
on that host. Access can be further controlled by using a `user-defined bridge
network`_ to connect the *httpexec* container to a subset of containers on the
host. In a non-container environment, firewall rules and VLANs should be
used to restrict access to an *httpexec* instance.


Command Isolation
-----------------

*httpexec* can only do what its target commands can do. Make sure it cannot
access dangerous commands. Access control is currently limited by directory
(see `Configuration`_). If necessary, create a directory containing only links
to allowed commands, and use that as ``EXEC_ROOT`` (``FOLLOW_LINKS`` must be
enabled). This is applicable to container and non-container environments.


Process Isolation
-----------------

By default, a Docker container (via `LXC`_) cannot access running processes or
start new processes on its host. Running *httpexec* inside a container limits
its scope to that container. In a non-container environment, this isolation
can be achieved via a virtual machine.


User Isolation
--------------

Docker best practices dictate that a container runs as a non-privileged user.
The UID the container is running as can only access host resources with the
same permissions as that UID on the host (the respective user names are
irrelevant). Ensure that the container does not run as ``root`` (UID ``0``).
Run the container as a UID that does not exist on the host for maximum
isolation. In both container and non-container environments, do not run
*httpexec* and/or the web server as a UID that has more access than is
necessary.


File Isolation
--------------

A Docker container does not have access to files on the host unless they are
explicitly mounted, and then its access is determined by the UID it is running
as (see above). This isolation can be achieved in a non-container environment
using `chroot`_ or a virtual machine.


Environment Isolation
---------------------

Environment variables are commonly used to store various credentials and other
privileged information. A Docker container does not have access to environment
variables on the host unless they explicitly exported to it, and this a
read-only static exchange (changes on the host will not be reflected in a
running container). Environment isolation can also be controlled by the web
server (see its documentation). *httpexec* also allows limited control over
the environment, but that is limited to modifying the environment, not
restricting access. While it is possible to unset specific environment
variables as seen by the target command, this requires prior knowledge of all
problematic variable names. In a non-container environment, a virtual
machine will ensure a strict separation of environments, but the VM itself may
contain privileged information.


===========
Development
===========

Use the project Makefile to simplify development tasks.

Setup
-----

Create a Python virtualenv environment and install the project and its ``dev``
dependencies in editable mode:

.. code-block:: console

    $ make dev


Run Checks
----------

Run all tests and linters:

.. code-block:: console

    $ make check


Build Documentation
-------------------

Build HTML documentation using `Sphinx`_:

.. code-block:: console

    $ make docs


Build Package
-------------

Build source and `wheel`_ packages. This will run all checks first.

.. code-block:: console

    $ make build


.. |python3.9| image:: https://img.shields.io/static/v1?label=python&message=3.9&color=informational
   :alt: Python 3.9
.. |python3.10| image:: https://img.shields.io/static/v1?label=python&message=3.10&color=informational
   :alt: Python 3.10
.. |python3.11| image:: https://img.shields.io/static/v1?label=python&message=3.11&color=informational
   :alt: Python 3.11
.. |release| image:: https://img.shields.io/github/v/release/mdklatt/httpexec?sort=semver
   :alt: GitHub release (latest SemVer)
.. |pypi| image:: https://img.shields.io/pypi/v/httpexec
   :alt: PyPI
   :target: `PyPI`_
.. |license| image:: https://img.shields.io/github/license/mdklatt/httpexec
   :alt: MIT License
   :target: `MIT License`_
.. |tests| image:: https://github.com/mdklatt/httpexec/actions/workflows/test.yml/badge.svg
    :alt: CI Test
    :target: `GitHub Actions`_


.. _ASGI-capable server: https://asgi.readthedocs.io/en/latest/implementations.html#servers
.. _Asynchronous Server Gateway Interface: https://asgi.readthedocs.io/en/latest
.. _base64: https://en.wikipedia.org/wiki/Base64
.. _base85: https://en.wikipedia.org/wiki/Ascii85
.. _chroot: https://en.wikipedia.org/wiki/Chroot
.. _GitHub Actions: https://github.com/mdklatt/httpexec/actions/workflows/test.yml
.. _Hypercorn: https://pgjones.gitlab.io/hypercorn
.. _LXC: https://linuxcontainers.org/
.. _MIT License: https://choosealicense.com/licenses/mit
.. _OpenAPI: https://www.openapis.org/
.. _PyPI: https://pypi.org/project/httpexec/
.. _Python logging: https://docs.python.org/3/howto/logging.html
.. _Semantic Versioning: https://semver.org/
.. _Sphinx: https://www.sphinx-doc.org/en/master/
.. _TOML: https://toml.io/en/
.. _user-defined bridge network: https://docs.docker.com/network/network-tutorial-standalone/#use-user-defined-bridge-networks
.. _wheel: https://peps.python.org/pep-0491/