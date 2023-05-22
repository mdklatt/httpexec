""" Test suite for the asgi module.

"""
from base64 import a85decode, a85encode, b64decode, b64encode
from http.client import OK, NOT_FOUND
from os import environ
from pathlib import Path

import pytest
from httpexec.asgi import *  # test __all__


@pytest.fixture
def client():
    """ Create a Quart test client.

    :yield: test client
    """
    environ.update({
        "QUART_TESTING": "1",
        "HTTPEXEC_EXEC_ROOT": str(Path.cwd() / "tests/assets/"),
    })
    return app.test_client()


@pytest.mark.asyncio
@pytest.mark.parametrize(("endpoint", "status"), (
    ("echo", OK),
    ("/echo", OK),  # Quart strips leading slashes
    ("../echo", NOT_FOUND),  # cannot leave root
    ("none", NOT_FOUND),  # no such command
))
async def test_endpoint(client, endpoint, status):
    """ Test endpoint handling.

    """
    response = await client.post(endpoint)
    assert response.status_code == status
    return


@pytest.mark.asyncio
@pytest.mark.parametrize("capture", (True, False))
@pytest.mark.parametrize(("scheme", "encode", "decode"), (
    ("base64", b64encode, b64decode),
    ("base85", a85encode, a85decode),
    (None, None, None),
))
async def test_params(client, capture, scheme, encode, decode):
    """ Test parameter handling.

    """
    data = "abc"
    stdin = encode(data.encode()).decode() if encode else data
    params = {
        "args": ["-o", "opt"],
        "stdin": {"content": stdin, "encode": scheme},
        "stderr": {"capture": capture, "encode": scheme},
        "stdout": {"capture": capture, "encode": scheme},
    }
    response = await client.post("echo", json=params)
    assert response.status_code == OK
    result = await response.json
    assert result["return"] == 0
    if not capture:
        return
    if decode:
        for key in ("stderr", "stdout"):
            result[key] = decode(result[key]).decode()
    assert "opt" in result["stderr"]
    assert result["stdout"] == data
    return


@pytest.mark.asyncio
@pytest.mark.parametrize(("follow", "status"), (
    (True, OK),
    (False, NOT_FOUND),
))
async def test_symlinks(client, tmp_path, follow, status):
    """ Test command execution with symbolic links.

    """
    app.config.update({
        "EXEC_ROOT": tmp_path,
        "FOLLOW_LINKS": follow
    })
    tmp_path.joinpath("link").symlink_to(Path.cwd() / "tests/assets/echo")
    response = await client.post("link")
    assert response.status_code == status
    return


# Make the script executable.

if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
