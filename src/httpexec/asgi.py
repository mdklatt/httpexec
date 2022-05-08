""" Implementation of the ASGI API.

"""
from asyncio.subprocess import create_subprocess_exec, PIPE
from base64 import b64decode, b64encode
from http.client import FORBIDDEN
from os import environ
from pathlib import Path
from quart import Quart, jsonify, request
from toml import load


__all__ = "app",


app = Quart(__name__)


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
    to the configured base path (*e.g.* `~ldm/bin`), or the response will be
    FORBIDDEN.

    :param command: command path to execute
    :return: response
    """
    # TODO: This is getting too long.
    pipes = dict.fromkeys(("stdin", "stdout", "stderr"), PIPE)
    params = await request.json or {}
    try:
        stdin = params["stdin"].encode()
        if params.get("stdin_encode", False):
            # Binary data was sent as transmittable text.
            stdin = b64decode(stdin)
    except KeyError:
        stdin = None
        pipes["stdin"] = None
    root = Path(app.config["EXEC_ROOT"]).resolve()  # EXEC_ROOT must be defined
    command = root.joinpath(command)
    if not app.config.get("FOLLOW_LINKS", False):
        # Command must be under root after following links.
        command = command.resolve()
    if not command.is_relative_to(root) or not command.is_file():
        # Only allow commands within the configured root path.
        return f"Access denied to `{command}`", FORBIDDEN
    argv = [str(command)] + params.get("args", [])
    process = await create_subprocess_exec(*argv, **pipes)
    stdout, stderr = await process.communicate(stdin)
    if params.get("stdout_encode", False):
        # Send data as transmittable text.
        stdout = b64encode(stdout)
    response = {
        "stdout": stdout.decode(),
        "stderr": stderr.decode(),  # should only be text
        "return": process.returncode,
    }
    return jsonify(response)
