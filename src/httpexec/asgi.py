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


_encoding_schemes = {
    "base64": (b64encode, b64decode),
    "base85": (a85encode, a85decode),
}


@app.before_first_request
async def config():
    """ Apply configuration settings to app.

    """
    # Environment variables take precedence over the config file. Config file
    # keys must be ALL CAPS and at the root level.
    #
    # This should not need to be marked async, but doing so causes no harm,
    # and, anecdotally, eliminates some reliability issues when `httpexec` is
    # running inside a Docker container that is being accessed by another
    # Docker container. Circumstantially, this is related to the use of the
    # `quart.utils.run_sync()` adapter to run a synchronous function.
    # See <https://github.com/mdklatt/httpexec/issues/1>.
    file = Path(environ.get("HTTPEXEC_CONFIG_PATH",  "etc/config.toml"))
    app.config.from_file(Path.cwd() / file, load)
    app.config.from_prefixed_env("HTTPEXEC")
    return


@app.route("/<path:command>", methods=["POST"])
async def run(command: str):
    """ Run an arbitrary command.

    The optional POST content is a JSON object with any of these attributes:

      "args":   a list of arguments to pass to `command`
      "stdin":  contents of STDIN to pipe to `command`
      "binary": an object specifying any binary encodings to use for "stdin"
                in this request and "stdout" or "stderr" in the response

    The response is a JSON object with these attributes:

      "return": the exit status returned by `command`
      "stdout": the contents of STDOUT from `command`
      "stderr": the contents of STDERR from `command`

    An HTTP status of `OK` does not mean that `command` itself was successful;
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
    params = await request.json or {}
    root = Path(app.config["EXEC_ROOT"]).resolve()
    command = root.joinpath(command)
    if int(app.config.get("FOLLOW_LINKS", 0)) == 0:
        # Command must be under root after following links. FOLLOW_LINKS can
        # come from a bool in the config file or an int environment variable.
        command = command.resolve()
    if not command.is_relative_to(root) or not command.is_file():
        # Only allow commands within the configured root path.
        return f"Access denied to `{command}`", FORBIDDEN
    argv = [str(command)] + params.get("args", [])
    stdin = params.get("stdin")
    binary = params.get("binary")
    return jsonify(await _exec(argv, stdin, binary))


async def _exec(argv: Sequence, stdin=None, binary=None):
    """  Execute a command on the host.

    :param argv: command arguments
    :param stdin: optional text value of stdin
    :param binary: mapping of binary encodings for I/O streams
    """
    pipes = dict.fromkeys(("stdout", "stderr"), PIPE)
    if not binary:
        binary = {}
    if stdin is not None:
        pipes["stdin"] = PIPE
        try:
            scheme = binary["stdin"]
        except KeyError:
            stdin = stdin.encode()
        else:
            decode = _encoding_schemes[scheme][1]
            stdin = decode(stdin)
    process = await create_subprocess_exec(*argv, **pipes)
    output = dict(zip(("stdout", "stderr"), await process.communicate(stdin)))
    for stream in set(output) & set(binary):
        encode = _encoding_schemes[binary[stream]][0]
        output[stream] = encode(output[stream])
    return {
        "stdout": output["stdout"].decode(),
        "stderr": output["stderr"].decode(),
        "return": process.returncode,
    }
