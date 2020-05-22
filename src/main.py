import time

import vault
from services import *
import logging

logger = logging.getLogger(__name__)


def main():
    """MAIN"""

    vault_url = vault.get_vault_url()
    vault_token = vault.get_vault_token()
    client = vault.get_connection(vault_url, vault_token)

    services = get_services_with_secrets()
    for service in services:
        labels = get_service_labels(service)
        secrets = get_service_secrets(service)

        for key, label in labels.items():
            if key.startswith("vault.secret"):
                logger.info(f"Found vault label on service: {service.short_id}")

                data, version = vault.get_secret_data_version(client, key, label)
                secret_version = get_docker_secret_version(secrets, label)

                if not secret_version or version > secret_version:
                    update_service_secret(service, data, version, label, key)

            elif key.startswith("vault.envvar"):
                logger.warning("vault.envvar is not implemented!")
                """
                data, version = vault.get_secret_data_version(client, label)
                secret_version = get_docker_secret_version(secrets, label)
                if version > secret_version:
                    update_service_secret(service, data, version, label)
                """

    logger.info("Going to sleep for 5min")
    time.sleep(5*60)


if __name__ == "__main__":
    main()
