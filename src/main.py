import os
import time
import sys

import vault
from services import *
import logging


def get_all_secrets_under_path(client, path, mount_point, secret_paths=[]):
    logging.info(f"Searching for secrets on path: {path}, mount_point: {mount_point}")
    response = client.secrets.kv.v2.list_secrets(path=path, mount_point=mount_point)
    keys = response.get("data", {}).get("keys", [])
    _path = path[:-1] if path.endswith("/") else path
    for key in keys:
        if key.endswith('/'):
            secret_paths += get_all_secrets_under_path(
                client, f"{_path}/{key}", mount_point, secret_paths=secret_paths
            )
        else:
            logging.info(f" - Found secret: {_path}/{key}")
            secret_paths += [f"{_path}/{key}"]
    return secret_paths


def read_service_secrets(client, service, key, label):
    logging.info(f"Found vault secrets label on service: {service.name} - ID: {service.short_id}")
    vault_secrets = []

    logging.info(f"Getting secret data version: {key}, {label}")
    data, version = vault.get_secret_data_version(client, key, label, mount_point="secrets")
    secrets = get_service_secrets(service)
    secret_version = get_docker_secret_version(secrets, label, key)

    if not secret_version or (version > secret_version):
        if label == "all":
            vault_secrets.extend(
                [
                    {"data": value, "version": version, "name": data_key, "path": key}
                    for data_key, value in data.items()
                ]
            )
        else:
            vault_secrets.append({"data": data[label], "version": version, "name": label, "path": key})

    return vault_secrets


def read_service_envvars(client, service, key, label, env_vars={}):
    logging.info(f"Found vault envvars label on service: {service.name} - ID: {service.short_id}")
    env_, _ = vault.get_secret_data_version(client, key, label, mount_point="envvars")
    env_vars.update(**env_)
    return env_vars


def main():
    """MAIN"""
    vault_url = vault.get_vault_url()
    client = vault.get_connection(vault_url)

    services = get_services_with_secrets()
    for service in services:
        logging.info(f"CHECKING TO UPDATE SECRETS FOR SERVICE: {service}")
        labels = get_service_labels(service)
        env_vars = {}
        vault_secrets = []
        for key, label in labels.items():
            if key.startswith("vault.secrets"):
                vault_secrets += read_service_secrets(client, service, key, label)

            elif key.startswith("vault.envvars"):
                env_vars = read_service_envvars(client, service, key, label, env_vars=env_vars)

            elif key.startswith("vault:"):
                root_path = key.split(":")[1]
                root_path = "/".join(root_path.split("."))
                # Load all from vault.secrets vault.envvars by recursing paths
                for mount_point in ["secrets", "envvars"]:
                    logging.info(f"Scanning vault for secrets on mount_point: {mount_point}")
                    paths = get_all_secrets_under_path(client, root_path, mount_point, secret_paths=[])
                    logging.info(f"Found secrets: {paths}")
                    for path in paths:
                        if mount_point == "envvars":
                            env_vars = read_service_envvars(client, service, path, "all", env_vars=env_vars)
                        elif mount_point == "secrets":
                            vault_secrets += read_service_secrets(client, service, path, "all")

        # Update the service
        update_service(service, env_vars, vault_secrets)

    sleep_length = os.environ.get("INTERVAL", 5 * 60)
    logging.info(f"Going to sleep for {sleep_length}s")
    time.sleep(sleep_length)


if __name__ == "__main__":
    log_level = os.environ.get("LOG_LEVEL", "INFO")
    logging.basicConfig(format="%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s",
                        level=getattr(logging, log_level))

    # Loop for a given number of times as specified in sys.argv[1] else forever
    run_loop = True
    counter = 1
    while run_loop:
        main()
        # Stop the loop if we are at the correct number of loops
        if (len(sys.argv) > 2):
            if (sys.arg[1] >= counter):
                run_loop = False
            counter += 1
