from time import sleep

import pytest
import docker
import os


@pytest.fixture()
def django_service():
    pass


@pytest.fixture()
def postgres_service():
    pass


@pytest.fixture()
def docker_service(vault_token):
    client = docker.from_env()
    network = client.networks.create(name=f"service_default", scope="swarm", driver="overlay", attachable=True)
    service_ = client.services.create(
        image="busybox:latest",
        command=["sleep", "infinity"],
        name="service",
        labels={"vault.secrets.test": "foo", "vault.envvars.test": "bar"}
    )

    while service_.tasks()[0].get("Status").get("State") != "running":
        sleep(1)

    yield service_

    service_.remove()
    network.remove()


@pytest.fixture(scope="session")
def image(root_path):
    import docker

    client = docker.from_env()
    dockerfile = os.path.join(root_path, "Dockerfile")

    image, logs = client.images.build(path=root_path, dockerfile=dockerfile, tag="vault-secrets:dev")

    yield image
