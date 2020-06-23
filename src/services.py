import datetime
from copy import deepcopy
from typing import Union, List, Optional

import docker
from docker.models.services import Service as DockerService
from docker.models.secrets import Secret as DockerSecret
from docker.types import SecretReference
import logging


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
    """Returns Docker services with labels that starts with 'vault.'"""

    client = docker.from_env()

    services = client.services.list()
    services = [
        service
        for service in services
        if any([label.startswith("vault") for label in get_service_labels(service).keys()])
    ]

    return services


def get_service_secrets(service: Union[DockerService, str]):
    service = id_to_service(service)

    secrets = service.attrs.get("Spec", {}).get("TaskTemplate", {}).get("ContainerSpec", {}).get("Secrets", None)
    return secrets


def get_docker_secret_version(secrets: List[dict], name: str, path: str) -> Optional[int]:
    if not secrets:
        return None

    if name == "all":
        for secret in secrets:
            secret_id = secret.get("SecretID")
            secret_labels = get_secret_labels(secret_id)
            path = path.replace(".", "/")
            if path == secret_labels.get("path"):
                return int(secret_labels.get("version", 0))

    for secret in secrets:
        if secret.get("SecretName", "").startswith(name):
            secret_id = secret.get("SecretID")
            version = get_secret_labels(secret_id).get("version", None)
            if version:
                return int(version)
            else:
                return None
    return None


def get_secret_labels(secret: Union[DockerSecret, str]) -> dict:
    secret = id_to_secret(secret)
    if secret:
        return secret.attrs["Spec"].get("Labels", {})
    else:
        return {}


def create_secret(secret_data: bytes, secret_name: str, version: int, vault_path: str) -> DockerSecret:
    """Create a Docker Secret"""

    client = docker.from_env()
    name = f"{secret_name}_{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
    vault_path = vault_path.replace(".", "/")
    existing_secret = get_existing_secrets(client, secret_name, version, vault_path)

    if existing_secret:
        return existing_secret

    secret = client.secrets.create(
        name=name,
        data=secret_data,
        labels={
            "version": str(version),
            "path": vault_path,
            "name": secret_name,
            "com.docker.stack.namespace": "compute",
        },
    )
    secret.reload()

    return secret


def get_existing_secrets(client, secret_name: str, version: int, vault_path: str) -> Optional[DockerSecret]:
    secrets = client.secrets.list()

    for secret in secrets:
        if {secret_name, str(version), vault_path} <= set(get_secret_labels(secret).values()):
            return secret


def get_service_environment_variables(service: DockerService) -> dict:
    env_list = service.attrs["Spec"].get("TaskTemplate", {}).get("ContainerSpec", {}).get("Env", [])
    return convert_env_list_to_dict(env_list)


def convert_dict_to_env_list(env_vars: dict) -> list:
    return [f"{key}={value}" for key, value in env_vars.items()]


def convert_env_list_to_dict(env_vars: list) -> dict:
    if env_vars:
        return {env.split("=")[0]: env.split("=")[1] for env in env_vars}
    else:
        return {}


def prepare_environment_variables(service: DockerService, vault_env: dict) -> list:
    env_vars = get_service_environment_variables(service)
    new_env = deepcopy(env_vars)
    new_env.update(vault_env)

    if env_vars == new_env:
        return []
    else:
        return convert_dict_to_env_list(new_env)


def prepare_secrets(vault_secrets: List[dict]) -> List[SecretReference]:
    new_secrets = []
    for secret in vault_secrets:
        new_secret = create_secret(secret["data"], secret["name"], secret["version"], secret["path"])
        new_secrets.append(SecretReference(new_secret.id, new_secret.name, filename=secret["name"]))

    return new_secrets


def update_service(service: DockerService, env_vars: dict, secrets: List[dict]) -> DockerService:
    """Bulk update a Docker service with new environment variables and secrets"""

    new_environment = new_secrets = None

    if env_vars:
        new_environment = prepare_environment_variables(service, env_vars)

    if secrets:
        new_secrets = prepare_secrets(secrets)

    if new_environment and new_secrets:
        service.update(env=new_environment, secrets=new_secrets)
        logging.info(
            f"Updated environment variables: {', '.join(env_vars.keys())} and "
            f"secrets: {', '.join([s['name'] for s in secrets])} for service: {service.short_id}"
        )
    elif new_environment:
        service.update(env=new_environment)
        logging.info(f"Updated environment variables: {', '.join(env_vars.keys())} for service: {service.short_id}")
    elif new_secrets:
        service.update(secrets=new_secrets)
        logging.info(f"Updated secrets: {', '.join([s['name'] for s in secrets])} for service: {service.short_id}")
    else:
        logging.info(f"Nothing updated for service: {service.short_id}")

    service.reload()
    return service
