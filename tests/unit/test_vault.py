import vault


def test_connect_to_vault(vault_service, vault_url, vault_token):

    client = vault.get_connection(vault_url)

    assert client.is_authenticated()


def test_write_secret(vault_client):
    client = vault_client
    response = client.secrets.kv.v2.create_or_update_secret(path="secret", secret={"test": "value"})

    assert response
    assert response["request_id"]


def test_read_secret(vault_client):
    client = vault_client
    client.secrets.kv.v2.create_or_update_secret(path="secret", secret={"test": "value"})

    response = client.secrets.kv.read_secret_version(path='secret')

    assert response
    assert response["data"]["data"] == {"test": "value"}


def test_get_secret_data_version(vault_client, secrets):
    path, secret = secrets
    data, version = vault.get_secret_data_version(vault_client, path, secret, "secrets")

    if ":" in secret:
        secret = secret.split(":")[-1]
    assert list(data.keys())[0] == secret
    assert version == 1
