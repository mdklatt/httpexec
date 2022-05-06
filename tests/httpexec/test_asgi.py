""" Test suite for the asgi module.

"""
from base64 import b64decode
from http.client import OK, FORBIDDEN

import pytest
from httpexec.asgi import *  # test __all__


@pytest.fixture
def client():
    """ Create a Quart test client.

    :yield: test client
    """
    app.config.from_mapping({
        "ROOT": "/bin"
    })
    yield app.test_client()
    for user_key in "ROOT", "UNSAFE":
        # Reset config after each test.
        try:
            del app.config[user_key]
        except KeyError:
            pass
    return


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
@pytest.mark.parametrize(("unsafe", "status"), (
    (True, OK),
    (False, FORBIDDEN),  # Quart strips leading slashes
))
async def test_command_symlink(client, tmp_path, unsafe, status):
    """ Test command execution with symbolic links.

    """
    app.config.from_mapping({
        "ROOT": tmp_path,
    })
    if unsafe:
        # Do not define value for safe requests to verify that requests are
        # safe by default.
        app.config["UNSAFE"] = True
    tmp_path.joinpath("ls").symlink_to("/bin/ls")
    response = await client.post("ls")
    assert response.status_code == status
    return


# Make the script executable.

if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
