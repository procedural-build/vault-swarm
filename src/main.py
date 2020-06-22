import os
import time

import vault
from services import *
import logging


def main():
    """MAIN"""
    vault_url = vault.get_vault_url()
    client = vault.get_connection(vault_url)

    services = get_services_with_secrets()
    for service in services:
        labels = get_service_labels(service)
        env_vars = {}
        vault_secrets = []
        for key, label in labels.items():
            if key.startswith("vault.secrets"):
                logging.info(f"Found vault secrets label on service: {service.name} - ID: {service.short_id}")

                data, version = vault.get_secret_data_version(client, key, label)
                secrets = get_service_secrets(service)
                secret_version = get_docker_secret_version(secrets, label, key)

                if not secret_version or version > secret_version:
                    if label == "all":
                        vault_secrets.extend(
                            [
                                {"data": value, "version": version, "name": data_key, "path": key}
                                for data_key, value in data.items()
                            ]
                        )
                    else:
                        vault_secrets.append({"data": data[label], "version": version, "name": label, "path": key})

            elif key.startswith("vault.envvars"):
                logging.info(f"Found vault envvars label on service: {service.name} - ID: {service.short_id}")
                env_, _ = vault.get_secret_data_version(client, key, label)
                env_vars.update(**env_)

        update_service(service, env_vars, vault_secrets)

    sleep_length = os.environ.get("INTERVAL", 5 * 60)
    logging.info(f"Going to sleep for {sleep_length}s")
    time.sleep(sleep_length)


if __name__ == "__main__":
    log_level = os.environ.get("LOG_LEVEL", "INFO")
    logging.basicConfig(format="%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s",
                        level=getattr(logging, log_level))
    main()
