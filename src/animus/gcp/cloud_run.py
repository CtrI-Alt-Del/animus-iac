import pulumi
import pulumi_gcp as gcp

from animus.config import Settings, resource_name


def _secret_env(
    secret_name: str, env_name: str, secrets: dict[str, object]
) -> dict[str, object]:
    return {
        "name": env_name,
        "value_source": {
            "secret_key_ref": {
                "secret": secrets["items"][secret_name]["secret_id"],
                "version": "latest",
            },
        },
    }


def _build_api_envs(
    settings: Settings,
    cloud_sql: dict[str, object],
    memorystore: dict[str, object],
    storage: dict[str, object],
    secrets: dict[str, object],
) -> list[dict[str, object]]:
    envs = [
        {"name": "ANIMUS_ENV", "value": settings.environment},
        {"name": "DB_NAME", "value": settings.database_name},
        {"name": "DB_USER", "value": settings.database_user},
        {
            "name": "DB_SOCKET_PATH",
            "value": pulumi.Output.concat("/cloudsql/", cloud_sql["connection_name"]),
        },
        {"name": "REDIS_HOST", "value": memorystore["host"]},
        {"name": "REDIS_PORT", "value": memorystore["port"].apply(str)},
        {"name": "FILES_BUCKET", "value": storage["bucket_name"]},
        {
            "name": "QDRANT_COLLECTION_PREFIX",
            "value": settings.qdrant_collection_prefix,
        },
        _secret_env("db-password", "DB_PASSWORD", secrets),
    ]

    optional_secret_envs = {
        "inngest-event-key": "INNGEST_EVENT_KEY",
        "onesignal-api-key": "ONESIGNAL_API_KEY",
        "qdrant-api-key": "QDRANT_API_KEY",
        "qdrant-url": "QDRANT_URL",
    }
    for secret_name, env_name in optional_secret_envs.items():
        if secrets["items"][secret_name]["has_version"]:
            envs.append(_secret_env(secret_name, env_name, secrets))

    return envs


def _cloud_run_service(
    resource_name_suffix: str,
    service_name: str,
    image: str,
    envs: list[dict[str, object]],
    settings: Settings,
    network: dict[str, object],
    cloud_sql: dict[str, object],
    iam: dict[str, object],
    dependencies: list[object],
) -> gcp.cloudrunv2.Service:
    return gcp.cloudrunv2.Service(
        resource_name_suffix,
        project=settings.gcp_project,
        name=service_name,
        location=settings.gcp_region,
        ingress="INGRESS_TRAFFIC_ALL",
        deletion_protection=settings.is_production,
        template={
            "service_account": iam["runtime_service_account_email"],
            "timeout": "300s",
            "scaling": {
                "min_instance_count": settings.cloud_run_min_instances,
            },
            "volumes": [
                {
                    "name": "cloudsql",
                    "cloud_sql_instance": {
                        "instances": [cloud_sql["connection_name"]],
                    },
                }
            ],
            "vpc_access": {
                "connector": network["vpc_connector_id"],
                "egress": "PRIVATE_RANGES_ONLY",
            },
            "containers": [
                {
                    "image": image,
                    "envs": envs,
                    "ports": {"container_port": 8080},
                    "resources": {
                        "limits": {
                            "cpu": "1",
                            "memory": "512Mi",
                        },
                    },
                    "volume_mounts": [
                        {
                            "name": "cloudsql",
                            "mount_path": "/cloudsql",
                        }
                    ],
                }
            ],
        },
        traffics=[
            {
                "type": "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST",
                "percent": 100,
            }
        ],
        opts=pulumi.ResourceOptions(depends_on=dependencies),
    )


def build_cloud_run_config(
    settings: Settings,
    network: dict[str, object],
    cloud_sql: dict[str, object],
    memorystore: dict[str, object],
    storage: dict[str, object],
    secrets: dict[str, object],
    iam: dict[str, object],
) -> dict[str, object]:
    dependencies = [
        *secrets["_secret_versions"].values(),
    ]
    api_service = _cloud_run_service(
        "cloud-run-api-service",
        resource_name("api", settings.stack),
        settings.api_image,
        _build_api_envs(settings, cloud_sql, memorystore, storage, secrets),
        settings,
        network,
        cloud_sql,
        iam,
        dependencies,
    )

    gcp.cloudrunv2.ServiceIamMember(
        "cloud-run-api-public-invoker",
        project=settings.gcp_project,
        location=settings.gcp_region,
        name=api_service.name,
        role="roles/run.invoker",
        member="allUsers",
        opts=pulumi.ResourceOptions(depends_on=[api_service]),
    )

    mlflow_service = None
    if settings.mlflow_enabled:
        mlflow_envs = [
            {
                "name": "DB_NAME",
                "value": settings.database_name,
            },
            {
                "name": "DB_USER",
                "value": settings.database_user,
            },
            {
                "name": "DB_SOCKET_PATH",
                "value": pulumi.Output.concat(
                    "/cloudsql/", cloud_sql["connection_name"]
                ),
            },
            {
                "name": "MLFLOW_ARTIFACT_ROOT",
                "value": pulumi.Output.concat(
                    "gs://", storage["bucket_name"], "/mlflow"
                ),
            },
            _secret_env("db-password", "DB_PASSWORD", secrets),
        ]
        mlflow_service = _cloud_run_service(
            "cloud-run-mlflow-service",
            resource_name("mlflow", settings.stack),
            settings.mlflow_image,
            mlflow_envs,
            settings,
            network,
            cloud_sql,
            iam,
            dependencies,
        )

    return {
        "service_name": api_service.name,
        "service_uri": api_service.uri,
        "location": settings.gcp_region,
        "min_instances": settings.cloud_run_min_instances,
        "ingress": "INGRESS_TRAFFIC_ALL",
        "mlflow_service_name": mlflow_service.name if mlflow_service else None,
        "mlflow_service_uri": mlflow_service.uri if mlflow_service else None,
    }
