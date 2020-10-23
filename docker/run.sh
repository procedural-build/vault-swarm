#!/usr/bin/env bash

export HOST_SRC_PATH="$(dirname "$(dirname "$(readlink -fm "$0")")")"/
echo "HOST SRC PATH = $HOST_SRC_PATH"

case "$1" in
  build)
    docker build --target production -t vault-swarm:latest $HOST_SRC_PATH
    ;;
  *)
  echo $"Usage: $0 {build}"
  exit 1
  ;;

esac
