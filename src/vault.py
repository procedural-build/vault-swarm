import os
from typing import Optional, Tuple

import hvac
import hvac.exceptions


def get_connection(url: str) -> hvac.Client:
    """Establish the Vault connection"""

    client = hvac.Client(url=url)
    authenticated_client = authenticate_vault(client)

    if not authenticated_client.is_authenticated():
        raise hvac.exceptions.Unauthorized("Unable to authenticate to the Vault service")

    return authenticated_client


def get_secret_data_version(client: hvac.Client, path: str, secret: str) -> Tuple[dict, int]:
    """Get a Vault secret and its version"""

    path = path.replace("vault.", "").split(".")
    mount_point = path[0]
    path = "/".join(path[1:])

    response = client.secrets.kv.v2.read_secret_version(path=path, mount_point=mount_point)
    version = response["data"]["metadata"]["version"]
    if secret == "all":
        data = response["data"]["data"]
    else:
        if ":" in secret:
            secret_, key = secret.split(":")
            data = {key: response["data"]["data"].get(secret_, None)}
        else:
            data = {secret: response["data"]["data"].get(secret, None)}

    return data, version


def get_vault_url() -> str:
    return os.environ.get("VAULT_ADDRESS", "http://0.0.0.0:8200")


def get_vault_token() -> Optional[str]:
    """Get a Vault token from enviroment or from /run/secrets/vault.token"""

    token = os.environ.get("VAULT_TOKEN", None)

    if token:
        return token

    if os.path.exists("/run/secrets/vault.token"):
        with open("/run/secrets/vault.token", "r") as file:
            token = file.read().strip()
        return token


def get_vault_user_password() -> Tuple[Optional[str], Optional[str]]:
    path = "/run/secrets/user_pass"

    if os.path.exists(path):
        with open(path, "r") as file:
            user, password = file.read().strip().split("\n")
        return user, password
    else:
        return None, None


def authenticate_vault(client: hvac.Client) -> hvac.Client:
    """
    Authenticate against vault.
    For EC2 purposed we can use AWS Auth
    For Dev purposed we can read a token from /run/secrets/vault.token or /run/secrets/user_pass
    """
    token = get_vault_token()
    if token:
        client.token = token
        return client

    user, password = get_vault_user_password()
    if user and password:
        client.auth_userpass(user, password)

    return client
