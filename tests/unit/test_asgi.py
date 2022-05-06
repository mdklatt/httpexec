""" Test suite for the asgi module.

"""
from base64 import b64decode
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
@pytest.mark.parametrize(("command", "status"), (
    ("ls", OK),
    ("/ls", OK),  # Quart strips leading slashes
    ("../ls", FORBIDDEN),  # cannot leave root
    ("does_not_exist", FORBIDDEN),
))
async def test_command(client, command, status):
    """ Test command execution.

    """
    params = {
        "args": ["-p"],
        "stdout_encode": True,
    }
    response = await client.post(command, json=params)
    assert response.status_code == status
    if status == OK:
        data = await response.json
        assert data["return"] == 0
        assert data["stderr"] == ""
        stdout = b64decode(data["stdout"]).decode()
        assert "tests/" in stdout.split("\n")
    return


@pytest.mark.asyncio
@pytest.mark.parametrize(("follow", "status"), (
    (True, OK),
    (False, FORBIDDEN),  # Quart strips leading slashes
))
async def test_symlinks(client, tmp_path, follow, status):
    """ Test command execution with symbolic links.

    """
    app.config.update({
        "EXEC_ROOT": tmp_path,
        "FOLLOW_LINKS": follow
    })
    tmp_path.joinpath("ls").symlink_to("/bin/ls")
    response = await client.post("ls")
    assert response.status_code == status
    return


# Make the script executable.

if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
