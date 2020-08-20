#!/usr/bin/env bash

function get_or_set_vault_address {
  if [ -z "$VAULT_ADDRESS" ]; then
    export VAULT_ADDRESS="https://vault.procedural.build"
  fi
}

case "$1" in
  build)
    docker build -t vault-swarm:latest .
    ;;
  cmd-dev)
    # Run a command with the source volume mounted (for development)
    get_or_set_vault_address
    docker run --rm -it \
      -e VAULT_ADDRESS=$VAULT_ADDRESS \
      -v $PWD/src:/app \
      -v $HOME/.secrets:/run/secrets \
     vault-swarm:latest $2
    ;;
  cmd)
    get_or_set_vault_address
    # Run a command with secrets volume mounted
    docker run --rm -it \
      -e VAULT_ADDRESS=$VAULT_ADDRESS \
      -v $HOME/.secrets:/run/secrets \
     vault-swarm:stable $2
    ;;
  *)
  echo $"Usage: $0 {build | cmd-dev | cmd }"
  exit 1
  ;;

esac
