import os
import time

import vault
from services import *
import logging

logger = logging.getLogger(__name__)


def main():
    """MAIN"""

    vault_url = vault.get_vault_url()
    client = vault.get_connection(vault_url)

    services = get_services_with_secrets()
    for service in services:
        labels = get_service_labels(service)
        env_vars = None
        vault_secrets = []
        for key, label in labels.items():
            if key.startswith("vault.secrets"):
                logger.info(f"Found vault secrets label on service: {service.short_id}")

                data, version = vault.get_secret_data_version(client, key, label)
                secrets = get_service_secrets(service)
                secret_version = get_docker_secret_version(secrets, label)

                if not secret_version or version > secret_version:
                    vault_secrets.append({"data": data[label], "version": version, "name": label, "path": key})

            elif key.startswith("vault.envvars"):
                logger.info(f"Found vault secrets label on service: {service.short_id}")
                env_vars, _ = vault.get_secret_data_version(client, key, label)

        update_service(service, env_vars, vault_secrets)

    sleep_length = os.environ.get("INTERVAL", 5*60)
    logger.info(f"Going to sleep for {sleep_length}s")
    time.sleep(sleep_length)


if __name__ == "__main__":
    main()
