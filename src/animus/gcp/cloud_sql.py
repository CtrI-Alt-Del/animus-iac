import pulumi
import pulumi_gcp as gcp

from animus.config import Settings, resource_name


def build_cloud_sql_config(
    settings: Settings,
    project_services: dict[str, object],
    network: dict[str, object],
    secrets: dict[str, object],
) -> dict[str, object]:
    instance_name = resource_name("postgres", settings.stack)
    private_services_connection = network["_private_services_connection_resource"]

    instance = gcp.sql.DatabaseInstance(
        "cloud-sql-instance",
        name=instance_name,
        database_version="POSTGRES_16",
        region=settings.gcp_region,
        deletion_protection=settings.is_production,
        settings=gcp.sql.DatabaseInstanceSettingsArgs(
            tier=settings.cloud_sql_tier,
            availability_type="REGIONAL" if settings.is_production else "ZONAL",
            backup_configuration=gcp.sql.DatabaseInstanceSettingsBackupConfigurationArgs(
                enabled=settings.cloud_sql_backups_enabled,
            ),
            ip_configuration=gcp.sql.DatabaseInstanceSettingsIpConfigurationArgs(
                ipv4_enabled=False,
                private_network=network["self_link"],
            ),
        ),
        opts=pulumi.ResourceOptions(
            depends_on=[*project_services["_resources"], private_services_connection]
        ),
    )

    database = gcp.sql.Database(
        "cloud-sql-database",
        project=settings.gcp_project,
        instance=instance.name,
        name=settings.database_name,
        charset="UTF8",
        collation="en_US.UTF8",
        deletion_policy="ABANDON" if settings.is_production else "DELETE",
        opts=pulumi.ResourceOptions(depends_on=[instance]),
    )

    user = gcp.sql.User(
        "cloud-sql-user",
        project=settings.gcp_project,
        instance=instance.name,
        name=settings.database_user,
        password=settings.database_password,
        deletion_policy="ABANDON" if settings.is_production else None,
        opts=pulumi.ResourceOptions(depends_on=[instance]),
    )

    return {
        "instance_name": instance.name,
        "database_version": instance.database_version,
        "region": instance.region,
        "tier": settings.cloud_sql_tier,
        "backups_enabled": settings.cloud_sql_backups_enabled,
        "private_network": network["self_link"],
        "connection_name": instance.connection_name,
        "private_ip_address": instance.private_ip_address,
        "database_name": database.name,
        "database_user": user.name,
        "database_password_secret_id": secrets["items"]["db-password"]["secret_id"],
    }
