import os
import time
import sys

import vault
import logging
import main


def get_or_create_folder(root_path):
    path = f"/run/secrets/{root_path}"
    if not os.path.exists(path):
        logging.info(f"Creating new folder for secrets at: {path}")
        os.makedirs(path)

    if not os.path.isdir(path):
        raise Exception(f"Path at {root_path} is not a folder!")

    return path


def write_envvars(envvars, root_path):
    path = get_or_create_folder(root_path)
    file = f"{path}/envvars"
    logging.info(f"Writing envvars to: {file}")
    with open(file, 'w') as f:
        for key, value in envvars.items():
            f.write(f"key=value")


def write_secrets(secrets, root_path):
    path = get_or_create_folder(root_path)
    for key, value in secrets.items():
        file = f"{path}/{key}"
        logging.info(f"Writing secret to: {file}")
        with open(file, 'w') as f:
            f.write(value)


def pull(root_path):
    """ Pull all secrets and envvars under vault path down to a local folder in
    /run/secrets/{root_path}/

    Note that envvars will be included in the secrets folder as a file named
    "envvars"
    """
    vault_url = vault.get_vault_url()
    client = vault.get_connection(vault_url)

    envvars = {}
    secrets = {}
    for mount_point in ["secrets", "envvars"]:
        logging.info(f"Scanning vault for secrets on mount_point: {mount_point}")
        paths = main.get_all_secrets_under_path(client, root_path, mount_point, secret_paths=[])
        logging.info(f"Found secrets: {paths}")
        for path in paths:
            data, version = vault.get_secret_data_version(client, path, "all", mount_point=mount_point)
            envvars.update(data) if mount_point == "envvars" else secrets.update(data)

    # Write the files
    write_envvars(envvars, root_path)
    write_secrets(secrets, root_path)
    logging.info(f"Done pulling secrets to: {root_path}")

if __name__ == "__main__":
    log_level = os.environ.get("LOG_LEVEL", "INFO")
    logging.basicConfig(format="%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s",
                        level=getattr(logging, log_level))

    # Loop for a given number of times as specified in sys.argv[1] else forever
    pull(*sys.argv[1:])
