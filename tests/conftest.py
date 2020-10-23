from time import sleep
import os

import docker
import pytest
from docker.types import EndpointSpec, NetworkAttachmentConfig

import vault


@pytest.fixture(scope="session")
def root_path():
    yield os.path.dirname(os.path.dirname(__file__))


@pytest.fixture()
def vault_service(vault_token):
    client = docker.from_env()
    network = client.networks.create(name=f"vault_default", scope="swarm", driver="overlay", attachable=True)
    vault_ = client.services.create(
        image="vault:1.4.1",
        command=["vault", "server", "--dev"],
        name="vault",
        env=[f"VAULT_DEV_ROOT_TOKEN_ID={vault_token}", f"VAULT_DEV_LISTEN_ADDRESS=0.0.0.0:8200"],
        endpoint_spec=EndpointSpec(ports={8200: 8200}),
        networks=[NetworkAttachmentConfig(target=network.id)]
    )

    while vault_.tasks()[0].get("Status").get("State") != "running":
        sleep(1)

    yield vault_

    vault_.remove()
    network.remove()


@pytest.fixture()
def vault_url():
    yield "http://0.0.0.0:8200"


@pytest.fixture()
def vault_token():
    token = "token"
    os.environ["VAULT_TOKEN"] = token
    yield token


@pytest.fixture()
def vault_client(vault_service, vault_url, vault_token):
    yield vault.get_connection(vault_url)
