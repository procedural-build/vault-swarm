from time import sleep

import docker
import pytest
from docker.types import SecretReference


@pytest.fixture()
def docker_secret():
    client = docker.from_env()
    secret = client.secrets.create(name="test", data=b'test data', labels={"version": "1"})
    secret.reload()
    yield secret

    secret.remove()


@pytest.fixture()
def docker_service(vault_token):
    client = docker.from_env()
    network = client.networks.create(name=f"service_default", scope="swarm", driver="overlay", attachable=True)
    service_ = client.services.create(
        image="busybox:latest",
        command=["sleep", "infinity"],
        name="service",
        labels={"label": "test"}
    )

    while service_.tasks()[0].get("Status").get("State") != "running":
        sleep(1)

    yield service_

    service_.remove()
    network.remove()


@pytest.fixture()
def service_with_secret(vault_token, docker_secret):
    client = docker.from_env()
    client.networks.prune()
    network = client.networks.create(name=f"secret_default", scope="swarm", driver="overlay", attachable=True)
    service_ = client.services.create(
        image="busybox:latest",
        command=["sleep", "infinity"],
        name="secret",
        labels={"vault.secrets": "test"},
        secrets=[SecretReference(docker_secret.id, docker_secret.name)]
    )

    while service_.tasks()[0].get("Status").get("State") != "running":
        sleep(1)

    yield service_

    service_.remove()
    network.remove()


@pytest.fixture()
def service_with_env_vars():
    client = docker.from_env()

    client.networks.prune()
    network = client.networks.create(name=f"environment_default", scope="swarm", driver="overlay", attachable=True)
    service_ = client.services.create(
        image="busybox:latest",
        command=["sleep", "infinity"],
        name="environment",
        labels={"vault.envvars.test": "TEST"},
        env=["KEEP_ME=true"]
    )

    while service_.tasks()[0].get("Status").get("State") != "running":
        sleep(1)

    yield service_

    service_.remove()
    network.remove()

