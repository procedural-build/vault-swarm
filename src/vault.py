import hvac
import os


def get_connection(url, token):
    client = hvac.Client(url=url, token=token)

    return client


def get_secret_data_version(client: hvac.Client, key: str, secret: str):

    path = key.replace("vault.secret.", "").replace(".", "/")
    response = client.secrets.kv.read_secret_version(path=path)
    version = response["data"]["metadata"]["version"]
    data = response["data"]["data"][secret]

    return data, version


def get_vault_url() -> str:
    return os.environ.get("VAULT_ADDRESS", "0.0.0.0:8200")


def get_vault_token() -> str:
    token = os.environ.get("VAULT_TOKEN", None)

    if token:
        return token
    else:
        return authenticate_vault()


def authenticate_vault():
    """
    Authenticate against vault.
    For EC2 purposed we can use AWS Auth
    For Dev purposed we can read a token from /run/secrets/token or /run/secrets/user and /run/secrets/pass
    """
    return ""
