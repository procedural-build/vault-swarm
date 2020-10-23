import docker
import time

from docker.types import Mount


def test_add_env():
    """Test that the correct environment variable gets added to a docker service"""


def test_update_env():
    """Test that an environment variable attached to a service can be updated"""


def test_remove_env():
    """Test that an environment variable attached to a service can be removed"""


def test_add_secret(image, vault_token, vault_service, vault_client, docker_service):
    """Test that a secret can be attached to a service"""

    response = vault_client.secrets.kv.v2.create_or_update_secret(path="test", mount_point="secrets", secret={"foo": "value"})
    response = vault_client.secrets.kv.v2.create_or_update_secret(path="test", mount_point="envvars", secret={"bar": "value"})

    client = docker.from_env()
    cmd = "python main.py 1"    # Only loop once in the test
    mounts = [Mount("/var/run/docker.sock", "/var/run/docker.sock", type="bind")]
    container = client.containers.run(
        image=image.tags[0], command=cmd, mounts=mounts,
        environment=["VAULT_ADDRESS=http://0.0.0.0:8200", f"VAULT_TOKEN={vault_token}"], stderr=True, detach=True,
        network_mode="host"
    )
    time.sleep(20)
    logs = container.logs().decode().split("\n")

    # get container
    container_id = docker_service.tasks()[-1].get("Status", {}).get("ContainerStatus", {}).get("ContainerID", None)
    service_container = client.containers.get(container_id)
    # assert that /run/secrets/foo is value
    code, result = service_container.exec_run("cat /run/secrets/foo")

    container.stop()
    container.remove()

    assert result.decode() == "value"
    assert "bar=value" in service_container.attrs["Config"]["Env"]


def test_update_secret():
    """Test that a secret attached to a service can be update"""


def test_remove_secret():
    """Test that a secret attached to a service can be removed"""
