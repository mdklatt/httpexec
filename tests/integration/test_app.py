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
def server(tmp_path_factory, unused_tcp_port_factory):
    """ Serve the app using Hypercorn.

    :yield: test client
    """
    config = tmp_path_factory.mktemp("test_app") / "config.toml"
    env = {
        "HTTPEXEC_CONFIG_PATH": str(config),
    }
    config.write_text(dumps({"EXEC_ROOT": "/bin"}))
    address = f"0.0.0.0:{unused_tcp_port_factory()}"
    command = f"{executable} -m hypercorn -b {address} httpexec.asgi:app"
    process = Popen(split(command), env=env)
    try:
        sleep(2.0)  # wait for app to start
        yield address
    finally:
        process.kill()
    return


@pytest.mark.asyncio
async def test_run(server):
    """ Verify that the application is running as expected

    """
    async with ClientSession(f"http://{server}") as session:
        params = {
            "stdout": {"capture": True},
        }
        async with session.post("/ls", json=params) as response:
            assert response.status == OK
            result = await response.json()
    assert result["return"] == 0
    assert "tests" in result["stdout"]["content"]
    return


# Make the script executable.

if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
