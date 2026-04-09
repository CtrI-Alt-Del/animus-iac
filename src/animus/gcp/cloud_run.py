import pulumi
import pulumi_gcp as gcp

from animus.config import Settings, resource_name


def _secret_value_env(
    secret_name: str, env_name: str, secrets: dict[str, object]
) -> dict[str, object]:
    return {
        "name": env_name,
        "value": secrets["items"][secret_name]["value"],
    }


def _build_api_envs(
    settings: Settings,
    cloud_sql: dict[str, object],
    memorystore: dict[str, object],
    storage: dict[str, object],
    secrets: dict[str, object],
) -> list[dict[str, object]]:
    envs = [
        {"name": "MODE", "value": settings.environment},
        {"name": "POSTGRES_DB", "value": settings.database_name},
        {"name": "POSTGRES_USER", "value": settings.database_user},
        {"name": "GCS_BUCKET_NAME", "value": storage["bucket_name"]},
        {
            "name": "REDIS_URL",
            "value": pulumi.Output.concat(
                "redis://",
                memorystore["host"],
                ":",
                pulumi.Output.from_input(memorystore["port"]).apply(str),
                "/0",
            ),
        },
        _secret_value_env("postgres-password", "POSTGRES_PASSWORD", secrets),
    ]

    optional_secret_envs = {
        "database-url": "DATABASE_URL",
        "gcs-emulator-host": "GCS_EMULATOR_HOST",
        "gemini-api-key": "GEMINI_API_KEY",
        "openai-api-key": "OPENAI_API_KEY",
        "google-client-id": "GOOGLE_CLIENT_ID",
        "pangea-service-url": "PANGEA_SERVICE_URL",
        "qdrant-url": "QDRANT_URL",
        "qdrant-api-key": "QDRANT_API_KEY",
        "inngest-event-key": "INNGEST_EVENT_KEY",
        "inngest-signing-key": "INNGEST_SIGNING_KEY",
        "jwt-secret-key": "JWT_SECRET_KEY",
        "jwt-algorithm": "JWT_ALGORITHM",
        "jwt-access-token-expiration-seconds": "JWT_ACCESS_TOKEN_EXPIRATION_SECONDS",
        "jwt-refresh-token-expiration-seconds": "JWT_REFRESH_TOKEN_EXPIRATION_SECONDS",
        "resend-api-key": "RESEND_API_KEY",
        "resend-sender-email": "RESEND_SENDER_EMAIL",
        "email-verification-secret-key": "EMAIL_VERIFICATION_SECRET_KEY",
        "email-verification-salt": "EMAIL_VERIFICATION_SALT",
        "email-verification-otp-ttl-seconds": "EMAIL_VERIFICATION_OTP_TTL_SECONDS",
        "email-verification-token-max-age-seconds": "EMAIL_VERIFICATION_TOKEN_MAX_AGE_SECONDS",
    }
    for secret_name, env_name in optional_secret_envs.items():
        if (
            secret_name in secrets["items"]
            and secrets["items"][secret_name]["has_value"]
        ):
            envs.append(_secret_value_env(secret_name, env_name, secrets))

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
    dependencies: list[object] = []
    animus_server_service = _cloud_run_service(
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
        name=animus_server_service.name,
        role="roles/run.invoker",
        member="allUsers",
        opts=pulumi.ResourceOptions(depends_on=[animus_server_service]),
    )

    return {
        "service_name": animus_server_service.name,
        "service_uri": animus_server_service.uri,
        "location": settings.gcp_region,
        "min_instances": settings.cloud_run_min_instances,
        "ingress": "INGRESS_TRAFFIC_ALL",
        "mlflow_service_name": None,
        "mlflow_service_uri": None,
    }
