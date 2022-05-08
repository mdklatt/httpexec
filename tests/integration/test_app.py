""" Integration tests for the httpexec app.

"""
import pytest
from aiohttp import ClientSession
from http.client import OK
from shlex import split
from subprocess import Popen
from sys import executable
from time import sleep
from toml import dumps


@pytest.fixture(scope="module")
def server(tmp_path_factory):
    """ Serve the app using Hypercorn.

    :yield: test client
    """
    config = tmp_path_factory.mktemp("test_app") / "config.toml"
    env = {
        "HTTPEXEC_CONFIG_PATH": str(config),
    }
    config.write_text(dumps({"EXEC_ROOT": "/bin"}))
    address = "0.0.0.0:8888"
    command = f"{executable} -m hypercorn -b {address} httpexec.asgi:app"
    process = Popen(split(command), env=env)
    try:
        sleep(0.5)  # wait for app to start
        yield address
    finally:
        process.kill()
    return


@pytest.mark.asyncio
async def test_run(server):
    """ Verify that the application is running as expected

    """
    async with ClientSession(f"http://{server}").post("/ls") as response:
        assert response.status == OK
        result = await response.json()
    assert result["return"] == 0
    assert "tests" in result["stdout"]
    return


# Make the script executable.

if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
