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
    label = "secret=test"
    secret_dict = {"SecretName": docker_secret.name, "SecretId": docker_secret.id}
    version = get_docker_secret_version([secret_dict], label)

    assert version == 1


def test_update_service_secret(service_with_secret):
    new_sercret = b"new data"
    updated_service = update_service_secret(service_with_secret, new_sercret, 2, "secret=test")

    assert updated_service
    assert updated_service.attrs["Spec"] != updated_service.attrs["PreviousSpec"]
