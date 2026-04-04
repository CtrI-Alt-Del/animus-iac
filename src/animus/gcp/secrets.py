import pulumi
import pulumi_gcp as gcp

from animus.config import Settings, secret_resource_id


def _create_secret(
    resource_name: str,
    logical_name: str,
    secret_value: pulumi.Input[str] | None,
    settings: Settings,
    project_services: dict[str, object],
) -> tuple[gcp.secretmanager.Secret, gcp.secretmanager.SecretVersion | None]:
    secret = gcp.secretmanager.Secret(
        resource_name,
        project=settings.gcp_project,
        secret_id=secret_resource_id(logical_name, settings.environment),
        deletion_protection=settings.is_production,
        replication={"auto": {}},
        labels={
            "app": "animus",
            "env": settings.environment,
        },
        opts=pulumi.ResourceOptions(depends_on=project_services["_resources"]),
    )

    version = None
    if secret_value is not None:
        version = gcp.secretmanager.SecretVersion(
            f"{resource_name}-version",
            secret=secret.id,
            secret_data=secret_value,
            deletion_policy="DISABLE",
            opts=pulumi.ResourceOptions(depends_on=[secret]),
        )

    return secret, version


def build_secrets_config(
    settings: Settings,
    project_services: dict[str, object],
) -> dict[str, object]:
    secret_specs = {
        "db-password": settings.database_password,
        "inngest-event-key": settings.inngest_event_key,
        "onesignal-api-key": settings.onesignal_api_key,
        "qdrant-api-key": settings.qdrant_api_key,
        "qdrant-url": settings.qdrant_url,
    }

    secret_resources: dict[str, gcp.secretmanager.Secret] = {}
    secret_versions: dict[str, gcp.secretmanager.SecretVersion] = {}
    rendered = {}

    for name, value in secret_specs.items():
        secret, version = _create_secret(
            f"secret-{name}",
            name,
            value,
            settings,
            project_services,
        )
        secret_resources[name] = secret
        rendered[name] = {
            "secret_id": secret.secret_id,
            "logical_name": f"{settings.secret_prefix}{name.replace('-', '_')}",
            "has_version": version is not None,
        }
        if version is not None:
            secret_versions[name] = version

    return {
        "prefix": settings.secret_prefix,
        "manager": "gcp-secret-manager",
        "single_source_of_truth": True,
        "items": rendered,
        "_secret_resources": secret_resources,
        "_secret_versions": secret_versions,
    }
