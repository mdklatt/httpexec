""" Test suite for the asgi module.

"""
from base64 import a85decode, a85encode, b64decode, b64encode
from http.client import OK, FORBIDDEN
from os import environ

import pytest
from httpexec.asgi import *  # test __all__


@pytest.fixture
def client():
    """ Create a Quart test client.

    :yield: test client
    """
    environ.update({
        "QUART_TESTING": "1",
        "HTTPEXEC_EXEC_ROOT": "/bin",
    })
    return app.test_client()


@pytest.mark.asyncio
@pytest.mark.parametrize(("endpoint", "status"), (
    ("cat", OK),
    ("/cat", OK),  # Quart strips leading slashes
    ("../cat", FORBIDDEN),  # cannot leave root
    ("does_not_exist", FORBIDDEN),
))
@pytest.mark.parametrize(("scheme", "encode", "decode"), (
    ("base64", b64encode, b64decode),
    ("base85", a85encode, a85decode),
))
async def test_command(client, endpoint, status, scheme, encode, decode):
    """ Test command execution.

    """
    params = {
        "args": ["-n"],
        "stdin": encode(b"abc").decode(),
        "binary": dict.fromkeys(("stdin", "stdout"), scheme)
    }
    response = await client.post(endpoint, json=params)
    assert response.status_code == status
    if status == OK:
        data = await response.json
        assert data["return"] == 0
        assert data["stderr"] == ""
        stdout = decode(data["stdout"]).decode()
        assert stdout.strip() == "1\tabc"
    return


@pytest.mark.asyncio
@pytest.mark.parametrize(("follow", "status"), (
    (True, OK),
    (False, FORBIDDEN),
))
async def test_symlinks(client, tmp_path, follow, status):
    """ Test command execution with symbolic links.

    """
    app.config.update({
        "EXEC_ROOT": tmp_path,
        "FOLLOW_LINKS": follow
    })
    tmp_path.joinpath("cat").symlink_to("/bin/cat")
    response = await client.post("cat")
    assert response.status_code == status
    return


# Make the script executable.

if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
