import os
from typing import Optional, Tuple
import logging
import hvac
import hvac.exceptions


def get_connection(url: str) -> hvac.Client:
    """Establish the Vault connection"""

    client = hvac.Client(url=url)
    authenticated_client = authenticate_vault(client)

    if not authenticated_client.is_authenticated():
        raise hvac.exceptions.Unauthorized("Unable to authenticate to the Vault service")
    else:
        logging.info("Vault client is authenticated")

    return authenticated_client


def get_secret_data_version(client: hvac.Client, path: str, secret: str, mount_point=None) -> Tuple[dict, int]:
    """Get a Vault secret and its version"""

    # Handle dot-separated paths (which must be fully qualified)
    if '.' in path:
        mount_point, path = get_vault_path(path, secret)

    response = client.secrets.kv.v2.read_secret_version(path=path, mount_point=mount_point)
    version = response.get("data", {}).get("metadata", {}).get("version", 0)
    if secret == "all":
        data = response.get("data", {}).get("data", None)
    else:
        if ":" in secret:
            secret_, key = secret.split(":")
            data = {key: response.get("data", {}).get("data", {}).get(secret_, None)}
        else:
            data = {secret: response.get("data", {}).get("data", {}).get(secret, None)}

    return data, version


def get_vault_url() -> str:
    return os.environ.get("VAULT_ADDRESS", "http://0.0.0.0:8200")


def get_vault_path(path: str, secret: str):
    path = path.replace("vault.", "").split(".")
    mount_point = path[0]
    if ":" in secret:
        secret = secret.split(":")[0]
    if secret == path[-1]:
        path.pop()
    path = "/".join(path[1:])

    return mount_point, path


def get_vault_token() -> Optional[str]:
    """Get a Vault token from environment or from /run/secrets/vault.token"""

    token = os.environ.get("VAULT_TOKEN", None)

    if token:
        return token

    if os.path.exists("/run/secrets/vault.token"):
        with open("/run/secrets/vault.token", "r") as file:
            token = file.read().strip()
        return token


def get_vault_user_password() -> Tuple[Optional[str], Optional[str]]:
    possible_cred_files = ["user_pass", "vault.userpass"]

    for cred_file in possible_cred_files:
        path = f"/run/secrets/{cred_file}"
        if os.path.exists(path):
            logging.info(f"Found vault credentials file {path}")
            with open(path, "r") as file:
                user, password = file.read().strip().split("\n")
            return user, password
        else:
            continue

    # Finally try to get this from the environment
    logging.info(f"Trying to get credentials from envvars VAULT_USR, VAULT_PSW: {os.environ}")
    return (
        os.environ.get('VAULT_USR', None),
        os.environ.get('VAULT_PSW', None)
    )


def authenticate_vault(client: hvac.Client) -> hvac.Client:
    """
    Authenticate against vault.
    For EC2 purposed we can use AWS Auth
    For Dev purposed we can read a token from /run/secrets/vault.token or /run/secrets/user_pass
    """
    token = get_vault_token()
    if token:
        logging.info("Authenticating with token")
        client.token = token
        return client

    user, password = get_vault_user_password()
    if user and password:
        logging.info("Authenticating with username and password")
        client.auth_userpass(user, password)

    return client
