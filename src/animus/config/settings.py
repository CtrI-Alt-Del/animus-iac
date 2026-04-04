from dataclasses import dataclass
from typing import Optional

import pulumi

from .naming import resource_name


@dataclass(frozen=True)
class Settings:
    stack: str
    environment: str
    is_production: bool
    gcp_project: str
    gcp_region: str
    resource_prefix: str
    secret_prefix: str
    secret_resource_prefix: str
    qdrant_collection_prefix: str
    cloud_run_min_instances: int
    cloud_sql_tier: str
    cloud_sql_backups_enabled: bool
    memorystore_tier: str
    memorystore_memory_size_gb: int
    storage_versioning_enabled: bool
    mlflow_enabled: bool
    database_name: str
    database_user: str
    database_password: pulumi.Output[str]
    api_image: str
    mlflow_image: str
    qdrant_url: Optional[pulumi.Output[str]]
    qdrant_api_key: Optional[pulumi.Output[str]]
    inngest_event_key: Optional[pulumi.Output[str]]
    onesignal_api_key: Optional[pulumi.Output[str]]
    github_repository: Optional[str]
    github_branch: Optional[str]


def load_settings() -> Settings:
    stack = pulumi.get_stack()
    app_config = pulumi.Config("animus")
    gcp_config = pulumi.Config("gcp")
    environment = app_config.get("env") or stack
    is_production = environment == "prod"

    qdrant_prefix = "" if is_production else f"{environment}_"

    return Settings(
        stack=stack,
        environment=environment,
        is_production=is_production,
        gcp_project=gcp_config.require("project"),
        gcp_region=gcp_config.require("region"),
        resource_prefix=resource_name("", stack).removesuffix("-"),
        secret_prefix=f"{environment}/",
        secret_resource_prefix=f"{environment}-",
        qdrant_collection_prefix=qdrant_prefix,
        cloud_run_min_instances=app_config.get_int("cloudRunMinInstances")
        or (1 if is_production else 0),
        cloud_sql_tier=app_config.get("cloudSqlTier")
        or ("db-g1-small" if is_production else "db-f1-micro"),
        cloud_sql_backups_enabled=app_config.get_bool("cloudSqlBackupsEnabled")
        if app_config.get_bool("cloudSqlBackupsEnabled") is not None
        else is_production,
        memorystore_tier=app_config.get("memorystoreTier")
        or ("STANDARD_HA" if is_production else "BASIC"),
        memorystore_memory_size_gb=app_config.get_int("memorystoreMemorySizeGb") or 1,
        storage_versioning_enabled=app_config.get_bool("storageVersioningEnabled")
        if app_config.get_bool("storageVersioningEnabled") is not None
        else is_production,
        mlflow_enabled=app_config.get_bool("mlflowEnabled")
        if app_config.get_bool("mlflowEnabled") is not None
        else not is_production,
        database_name=app_config.get("databaseName") or "animus",
        database_user=app_config.get("databaseUser") or "animus",
        database_password=app_config.require_secret("dbPassword"),
        api_image=app_config.get("apiImage")
        or "us-docker.pkg.dev/cloudrun/container/hello",
        mlflow_image=app_config.get("mlflowImage")
        or "us-docker.pkg.dev/cloudrun/container/hello",
        qdrant_url=app_config.get_secret("qdrantUrl"),
        qdrant_api_key=app_config.get_secret("qdrantApiKey"),
        inngest_event_key=app_config.get_secret("inngestEventKey"),
        onesignal_api_key=app_config.get_secret("onesignalApiKey"),
        github_repository=app_config.get("githubRepository"),
        github_branch=app_config.get("githubBranch"),
    )
