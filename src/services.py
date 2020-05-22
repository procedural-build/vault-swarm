import datetime
from typing import Union, List, Optional

import docker
from docker.models.services import Service as DockerService
from docker.models.secrets import Secret as DockerSecret
from docker.types import SecretReference
import logging

logger = logging.getLogger(__name__)


def id_to_service(service: Union[DockerService, str]) -> DockerService:
    if isinstance(service, str):
        client = docker.from_env()
        return client.services.get(service)
    else:
        return service


def id_to_secret(secret: Union[DockerSecret, str]) -> DockerSecret:
    if isinstance(secret, str):
        client = docker.from_env()
        return client.secrets.get(secret)
    else:
        return secret


def get_service_labels(service: Union[DockerService, str]) -> dict:
    service = id_to_service(service)

    return service.attrs["Spec"]["Labels"]


def get_services_with_secrets():
    client = docker.from_env()

    services = client.services.list()

    return services


def get_service_secrets(service: Union[DockerService, str]):
    service = id_to_service(service)

    secrets = service.attrs.get("Spec", {}).get("TaskTemplate", {}).get("ContainerSpec", {}).get("Secrets", None)
    return secrets


def get_docker_secret_version(secrets: List[dict], name: str) -> Optional[int]:
    if not secrets:
        return None

    for secret in secrets:
        if secret.get("SecretName", "").startswith(name):
            secret_id = secret.get("SecretId")
            version = get_secret_labels(secret_id).get("version", None)
            if version:
                return int(version)
            else:
                return None
    return None


def get_secret_labels(secret: Union[DockerSecret, str]) -> dict:
    secret = id_to_secret(secret)
    return secret.attrs["Spec"]["Labels"]


def update_service_secret(service: DockerService, data: bytes, version: int, name: str, path: str) -> DockerService:
    """Update a secret connected to a Docker Service"""

    secret = create_secret(data, name, version, path)
    service.update(secrets=[SecretReference(secret.id, secret.name, filename=name)])
    service.reload()

    logger.info(f"Updated secret: {secret.name} for service: {service.short_id}")
    return service


def create_secret(secret_data: bytes, secret_name: str, version: int, vault_path: str) -> DockerSecret:
    """Create a Docker Secret"""

    client = docker.from_env()
    name = f"{secret_name}_{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
    vault_path = vault_path.replace(".", "/")
    secret = client.secrets.create(
        name=name, data=secret_data, labels={"version": str(version), "path": vault_path}
    )
    secret.reload()

    return secret
