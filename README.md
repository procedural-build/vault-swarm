# VAULT DOCKER SECRETS

* Runs as a contianer and listens to vault for secrets
* If it finds new secrets it will update the corresponding local docker secrets
* Similar to Watchtower


Should have access to the docker socket so it knows all services and secrets running.
Based on [hvac](https://github.com/hvac/hvac) and [docker-py](https://github.com/docker/docker-py) 

Authenticates with Vault either with a token (for dev purposes) or through the Vault EC2 mechanism
