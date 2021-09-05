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
def vault_enable_secrets(vault_client):
    vault_client.sys.enable_secrets_engine(
        backend_type='kv',
        path='secrets',
        options={"version": 2}
    )


@pytest.fixture()
def vault_secret(vault_client, vault_enable_secrets):
    response = vault_client.secrets.kv.v2.create_or_update_secret(path="test", secret={"test": "test data"},
                                                                  mount_point="secrets")
    yield response


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


@pytest.fixture(params=[("test", "test"), ("test", "test:newname"), ("test:test2", "test2:newname2")],
                ids=["test - test", "test - test:newname", "test:test2 - test2:newname"])
def secrets(request, vault_client, vault_enable_secrets):
    vault_client.secrets.kv.v2.create_or_update_secret(path="test", secret={"test": "test data", "test2": "test data2"},
                                                       mount_point="secrets")
    yield request.param
