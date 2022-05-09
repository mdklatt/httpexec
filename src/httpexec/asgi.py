""" Implementation of the ASGI API.

"""
from asyncio.subprocess import create_subprocess_exec, PIPE
from base64 import a85decode, a85encode, b64decode, b64encode
from http.client import FORBIDDEN
from os import environ
from pathlib import Path
from quart import Quart, jsonify, request
from toml import load
from typing import Sequence


__all__ = "app",


app = Quart(__name__)


_decodings = {
    "base64": b64decode,
    "base85": a85decode,
}


_encodings = {
    "base64": b64encode,
    "base85": a85encode,
}


@app.before_first_request
def config():
    """ Get configuration settings.

    """
    # Environment variables take precedence over the config file. Config file
    # keys must be ALL CAPS and at the root level.
    file = Path(environ.get("HTTPEXEC_CONFIG_PATH",  "etc/config.toml"))
    app.config.from_file(Path.cwd() / file, load)
    app.config.from_prefixed_env("HTTPEXEC")
    return


@app.route("/<path:command>", methods=["POST"])
async def run(command):
    """ Run an arbitrary command.

    The request content must be a JSON object with an "args" attribute whose
    value is a list of arguments to pass to `command` and an
    optional "stdin" attribute that is a base64-encoded data string that will
    be passed to the command vi STDIN.

    The response will be the base64-encoded contents of STDOUT; the contents of
    STDIN as text; and the process return code. An HTTP status code of OK only
    means that a valid response was returned, *NOT* that the underlying command
    was successful.

    The first value of "argv" is the command to execute; this must be relative
    to the configured root path or the response will be FORBIDDEN.

    :param command: command path to execute
    :return: response
    """
    params = await request.json or {}
    root = Path(app.config["EXEC_ROOT"]).resolve()  # EXEC_ROOT must be defined
    command = root.joinpath(command)
    if not app.config.get("FOLLOW_LINKS", False):
        # Command must be under root after following links.
        command = command.resolve()
    if not command.is_relative_to(root) or not command.is_file():
        # Only allow commands within the configured root path.
        return f"Access denied to `{command}`", FORBIDDEN
    argv = [str(command)] + params.get("args", [])
    stdin = params.get("stdin")
    binary = params.get("binary")
    return jsonify(await _exec(argv, stdin, binary))


async def _exec(argv: Sequence, stdin=None, binary=None):
    """ Execute a command on the host.

    :param argv: command arguments
    :param stdin: optional text value of stdin
    :param binary: mapping of binary encodings for I/O streams
    """
    pipes = dict.fromkeys(("stdout", "stderr"), PIPE)
    if stdin is not None:
        pipes["stdin"] = PIPE
        stdin = _decodings["stdin"](stdin) if "stdin" in binary else stdin.encode()
    process = await create_subprocess_exec(*argv, **pipes)
    output = dict(zip(("stdout", "stderr"), await process.communicate(stdin)))
    for stream in set(output) & set(binary or {}):
        output[stream] = _encodings[binary[stream]](output[stream])
    return {
        "stdout": output["stdout"].decode(),
        "stderr": output["stderr"].decode(),
        "return": process.returncode,
    }
