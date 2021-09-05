import docker

from services import *


def test_get_secrets(docker_secret):
    client = docker.from_env()
    secrets = client.secrets.list()

    assert secrets
    assert docker_secret.id in [s.id for s in secrets]


def test_get_services(docker_service):
    client = docker.from_env()

    services_ = client.services.list()

    assert services_
    assert docker_service.id in [s.id for s in services_]


def test_get_service_labels(docker_service):
    assert get_service_labels(docker_service) == {"label": "test"}


def test_get_services_with_secrets(docker_service, service_with_secret):
    services_ = get_services_with_secrets()

    assert services_
    assert len(services_) == 1


def test_get_service_secrets(service_with_secret):
    secrets = get_service_secrets(service_with_secret)
    assert secrets


def test_get_docker_secret_version(docker_secret):
    label = "test"
    secret_dict = {"SecretName": docker_secret.name, "SecretId": docker_secret.id}
    version = get_docker_secret_version([secret_dict], label)

    assert version == 1


def test_read_service_secrets(vault_client, docker_service, vault_secret):
    secret = read_service_secrets(vault_client, docker_service, "test", "test:/path/to/secret.pw")

    assert secret
    assert isinstance(secret, list)
    assert {"data", "version", "name", "path"} == set(secret[0].keys())


def test_create_secret():
    secret = create_secret(b"some data", "test_secret", 1,
                  "vault.secrets.ssl-certificates.archive.sustainabilitytool-net:privkey1.pem", "my-test-stack")

    assert secret