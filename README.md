# VAULT SWARM

Store your secrets in [HashiCorp Vault](https://www.vaultproject.io) and let Vault Swarm retrieve it for you and 
configure your Docker Swarm Services for you. 

## Docker Stack Example
In the example below we use Vault Swarm to attach a Docker secret to `my_app`. Vault Swarm will look for the secret in Vault
at the path `secrets/foo` and return you the secret with key `secret`.
Vault Swarm will also add an environment variable to `my_app` called `KEY`, which it will find at the path `envvars/bar` in Vault.

```yaml
version: 3.8

services:
  vault:
    image: vault-swarm:latest
    secrets:
      - vault.token
    environment:
      VAULT_ADDRESS: http://0.0.0.0:8200
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock

  my_app:
    image: ubuntu:latest
    deploy:
      labels:
        - vault.secrets.foo=secret
        - vault.envvars.bar=KEY

secrets:
  vault.token:
    file: $HOME/.secrets/vault.token
```

## Fetching Multiple Secrets
If you have specified more than a single key to a path in Vault you can use 
```
   labels:
     - vault.secrets.foo=all
     - vault.envvars.bar=all

```
to retrieve them all.

## Renaming values
By default Vault Swarm creates a secret/env var with the same name as the key in Vault. 
If you want change the name you can do so with `vault.secrets.foo=old_name:new_name`
In the example below we have saved the value `guest_user` in Vault at `envvars/database/DB_USER`. 
`my_app` expects it as an environment variable called `DB_USER` but our postgres container expects it as `POSTGRES_USER`.

```yaml
version: 3.8

services:
  my_db:
    image: postgres:latest
    deploy:
      labels:
        - vault.envvars.database=DB_USER:POSTGRES_USER

  my_app:
    image: ubuntu:latest
    deploy:
      labels:
        - vault.envvars.database=DB_USER
```

## Authentication
Vault Swarm currently supports three ways of authenticating with Vault: `token, user/pass, EC2`

### Token
Supply the token either as a environment variable `VAULT_TOKEN` or put it in a Docker secret called `vault.token`.

### User/Password
Supply the user and password as a Docker secret called `user_pass`. The contents of `user_pass` should be:
```
username
password
```

### EC2
WIP

## Configuration
Vault swarm is configurable through a number of environment variables:

| KEY               | DEFAULT       | DESCRIPTION       |
| ----------------- | ------------- | ----------------- | 
| LOG_LEVEL         | INFO          | Sets the logging level. Accepts: DEBUG/INFO/WARNING/ERROR |
| VAULT_ADDRESS     | http://0.0.0.0:8200          | The address of your vault deployment. |
| VAULT_TOKEN       | None          | The access token |  

## Development
Vault Swarm is written in Python 3.8 and uses `pipenv` as its package manager. 
Install the dependencies with:
```
pipenv install
```

### Tests
Run the tests with:

```
pytest tests/
```
