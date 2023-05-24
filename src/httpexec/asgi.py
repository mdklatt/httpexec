""" Implementation of the ASGI API.

"""
from __future__ import annotations

from asyncio.subprocess import create_subprocess_exec, DEVNULL, PIPE
from base64 import a85decode, a85encode, b64decode, b64encode
from http.client import NOT_FOUND
from importlib import resources
from os import environ
from pathlib import Path
from quart import Quart, jsonify, request
from toml import loads  # TODO: tomllib in Python 3.11+
from typing import Sequence


__all__ = "app",


app = Quart(__name__)


_encoding_schemes = {
    "base64": (b64encode, b64decode),
    "base85": (a85encode, a85decode),
}


@app.before_first_request
async def config():
    """ Apply configuration settings to app.

    Default configuration settings can be overridden with a user-supplied
    TOML file and/or environment variables. Environment variables have the
    highest precedence. Configuration file settings must be at the root level,
    and the keys must be ALL CAPS.

    """
    # This should not need to be marked async, but doing so causes no harm,
    # and, anecdotally, eliminates some reliability issues when `httpexec` is
    # running inside a Docker container that is being accessed by another
    # Docker container. Circumstantially, this is related to the use of the
    # `quart.utils.run_sync()` adapter to run a synchronous function.
    # See <https://github.com/mdklatt/httpexec/issues/1>.
    defaults = resources.files("httpexec").joinpath("etc/defaults.toml")
    config = loads(defaults.read_text())
    try:
        path = Path(environ["HTTPEXEC_CONFIG_PATH"])
    except KeyError:
        pass
    else:
        config |= loads(path.read_text())
    app.config.from_mapping(config)
    app.config.from_prefixed_env("HTTPEXEC")
    app.logger.setLevel(app.config.get("LOGGING_LEVEL"))
    return


@app.route("/<path:command>", methods=["POST"])
async def run(command: str):
    """ Run an arbitrary command.

    The optional POST content is a JSON object with any of these optional
    attributes:

      "args":        a list of arguments to pass to `command`
      "streams":     an object defining the parameters for `stdin`, `stderr`,
                     and`stdout`
      "environment": an object defining environment variable overrides

    The response is a JSON object with these attributes:

      "return": the exit status returned by the command
      "stderr": the contents of STDERR from the command if `capture: true`
      "stdout": the contents of STDOUT from the command if `capture: true`

    An HTTP status of `OK` does not mean that the command itself succeeded;
    always check the value of "return" in the response object.

    If the contents of STDIN, STDERR, or STDOUT ar binary, they must be encoded
    as text for transmission. The "binary" object in the request is used to
    specify the scheme to use for each stream, if any. Each stream can use a
    different scheme. The supported schemes are "base64" and "base85".

    The client must encode "stdin" from binary to text before sending the
    request and decode "stdout" and/or "stderr" from text to binary after
    receiving the response.

    :param command: command path to execute
    :return: response
    """
    root = Path(app.config["EXEC_ROOT"]).resolve()
    command = root.joinpath(command)
    if int(app.config.get("FOLLOW_LINKS", 0)) == 0:
        # FOLLOW_LINKS can come from a bool in the config file or an int
        # environment variable. By default, a link cannot be used to escape
        # EXEC_ROOT. If FOLLOW_LINKS is true, only the link itself must be
        # under EXEC_ROOT.
        command = command.resolve()
    if not (command.is_relative_to(root) and command.is_file()):
        # Only allow commands within the configured root path.
        return f"Command `{command}` not found", NOT_FOUND
    params = await request.json or {}
    argv = [str(command)] + params.get("args", [])
    streams = {key: params.get(key, {}) for key in ("stdin", "stderr", "stdout")}
    env = params.get("environment", {})
    result = await _exec(argv, streams, env)
    return jsonify(result)


async def _exec(argv: Sequence, streams: dict, env: dict) -> dict:
    """  Execute a command on the host.

    STDIN is decoded if necessary before executing the command, and STDERR
    and STDOUT are encoded for transmission back to the client.

    :param argv: command line arguments
    :param streams: STDIN, STDERR, and STDOUT parameters
    :param env: mapping of environment variable overrides
    """
    pipes = {key: PIPE if streams[key].get("capture", False) else DEVNULL
             for key in ("stderr", "stdout")}
    stdin = streams["stdin"].get("content")
    if stdin is not None:
        pipes["stdin"] = PIPE
        scheme = streams["stdin"].get("encode")
        if scheme is None:
            stdin = stdin.encode()
        else:
            decode = _encoding_schemes[scheme][1]
            stdin = decode(stdin)
    env = environ | env  # update parent environment
    process = await create_subprocess_exec(*argv, **pipes, env=env)
    output = dict(zip(("stdout", "stderr"), await process.communicate(stdin)))
    for key, content in output.items():
        if content is None:
            continue
        scheme = streams[key].get("encode")
        if scheme is not None:
            encode = _encoding_schemes[scheme][0]
            content = encode(content)
        output[key] = {
            "content": content.decode(),
            "encode": scheme,
        }
    return output | {"return": process.returncode}
