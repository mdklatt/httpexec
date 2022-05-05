""" Test suite for the asgi module.

"""
from base64 import b64decode
from http.client import OK, FORBIDDEN
from pathlib import Path
from sys import executable


import pytest
from httpexec.asgi import *  # test __all__


@pytest.fixture
def client():
    """ Create a Quart test client.

    :yield: test client
    """
    app.config.from_mapping({
        "ROOT": Path(executable).parent
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
@pytest.mark.parametrize(("command", "unsafe", "status"), (
    ("python", True, OK),
    ("/python", True, OK),  # Quart strips leading slashes
    ("../python", True, FORBIDDEN),  # don't escape root
    ("does_not_exist", True, FORBIDDEN),
    ("python", False, FORBIDDEN),
))
async def test_command(client, command, unsafe, status):
    """ Test command execution.

    """
    params = {
        "args": ["-m", "pip", "--version"],
        "stdout_encode": True,
    }
    if unsafe:
        # Do not define value for safe requests to verify that requests are
        # safe by default.
        app.config["UNSAFE"] = True
    response = await client.post(command, json=params)
    assert response.status_code == status
    if status == OK:
        data = await response.json
        assert data["return"] == 0
        assert data["stderr"] == ""
        stdout = b64decode(data["stdout"]).decode()
        assert stdout.find("pip") != -1
    return


# Make the script executable.

if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
