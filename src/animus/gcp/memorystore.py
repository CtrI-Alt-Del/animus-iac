import pulumi
import pulumi_gcp as gcp

from animus.config import Settings, resource_name


def build_memorystore_config(
    settings: Settings,
    project_services: dict[str, object],
    network: dict[str, object],
) -> dict[str, object]:
    instance_id = resource_name("redis", settings.stack)
    private_services_connection = network["_private_services_connection_resource"]

    instance = gcp.redis.Instance(
        "memorystore-instance",
        name=instance_id,
        display_name=instance_id,
        region=settings.gcp_region,
        tier=settings.memorystore_tier,
        memory_size_gb=settings.memorystore_memory_size_gb,
        authorized_network=network["id"],
        connect_mode="PRIVATE_SERVICE_ACCESS",
        redis_version="REDIS_7_2",
        opts=pulumi.ResourceOptions(
            depends_on=[*project_services["_resources"], private_services_connection]
        ),
    )

    return {
        "instance_id": instance.name,
        "host": instance.host,
        "port": instance.port,
        "region": instance.region,
        "tier": settings.memorystore_tier,
        "memory_size_gb": settings.memorystore_memory_size_gb,
        "authorized_network": network["id"],
        "connect_mode": "PRIVATE_SERVICE_ACCESS",
    }
