from .artifact_registry import build_artifact_registry_config
from .cloud_run import build_cloud_run_config
from .cloud_sql import build_cloud_sql_config
from .iam import build_identity_config
from .memorystore import build_memorystore_config
from .network import build_network_config
from .secrets import build_secrets_config
from .services import enable_services
from .storage import build_storage_config
from animus.config import Settings


def deploy(settings: Settings) -> dict[str, dict[str, object]]:
    services = enable_services(settings)
    network = build_network_config(settings, services)
    artifact_registry = build_artifact_registry_config(settings, services)
    storage = build_storage_config(settings, services)
    secrets = build_secrets_config(settings, services)
    iam = build_identity_config(settings, services, secrets)
    cloud_sql = build_cloud_sql_config(settings, services, network, secrets)
    memorystore = build_memorystore_config(settings, services, network)
    cloud_run = build_cloud_run_config(
        settings,
        network,
        cloud_sql,
        memorystore,
        storage,
        secrets,
        iam,
    )

    return {
        "services": {
            key: value for key, value in services.items() if not key.startswith("_")
        },
        "network": {
            key: value for key, value in network.items() if not key.startswith("_")
        },
        "artifact_registry": artifact_registry,
        "iam": iam,
        "cloud_run": cloud_run,
        "cloud_sql": cloud_sql,
        "memorystore": memorystore,
        "storage": storage,
        "secrets": {
            key: value for key, value in secrets.items() if not key.startswith("_")
        },
    }
