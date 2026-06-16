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
    cloud_sql_edition: str
    cloud_sql_backups_enabled: bool
    memorystore_tier: str
    memorystore_memory_size_gb: int
    storage_versioning_enabled: bool
    mlflow_enabled: bool
    database_name: str
    database_user: str
    database_password: pulumi.Input[str]
    database_url: Optional[pulumi.Input[str]]
    gcs_emulator_host: Optional[pulumi.Input[str]]
    gemini_api_key: Optional[pulumi.Input[str]]
    openai_api_key: Optional[pulumi.Input[str]]
    google_client_id: Optional[pulumi.Input[str]]
    pangea_service_url: Optional[pulumi.Input[str]]
    jwt_secret_key: Optional[pulumi.Input[str]]
    jwt_algorithm: Optional[pulumi.Input[str]]
    jwt_access_token_expiration_seconds: Optional[pulumi.Input[str]]
    jwt_refresh_token_expiration_seconds: Optional[pulumi.Input[str]]
    resend_api_key: Optional[pulumi.Input[str]]
    resend_sender_email: Optional[pulumi.Input[str]]
    email_verification_secret_key: Optional[pulumi.Input[str]]
    email_verification_salt: Optional[pulumi.Input[str]]
    email_verification_otp_ttl_seconds: Optional[pulumi.Input[str]]
    email_verification_token_max_age_seconds: Optional[pulumi.Input[str]]
    api_image: str
    mlflow_image: str
    qdrant_url: Optional[pulumi.Input[str]]
    qdrant_api_key: Optional[pulumi.Input[str]]
    inngest_event_key: Optional[pulumi.Input[str]]
    inngest_signing_key: Optional[pulumi.Input[str]]
    onesignal_api_key: Optional[pulumi.Input[str]]
    supabase_storage_bucket: Optional[str]
    reset_password_otp_ttl_seconds: Optional[str]
    reset_password_otp_resend_cooldown_seconds: Optional[str]
    reset_password_context_ttl_seconds: Optional[str]
    supabase_url: Optional[str]
    supabase_key: Optional[pulumi.Input[str]]
    onesignal_app_id: Optional[str]
    onesignal_rest_api_key: Optional[pulumi.Input[str]]
    iam_user_email: Optional[str]
    github_repository: Optional[str]
    github_branch: Optional[str]


def load_settings() -> Settings:
    def _config_secret(
        config: pulumi.Config,
        config_key: str,
    ) -> Optional[pulumi.Input[str]]:
        return config.get_secret(config_key)

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
        cloud_sql_edition=app_config.get("cloudSqlEdition") or "ENTERPRISE",
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
        database_url=_config_secret(app_config, "databaseUrl"),
        gcs_emulator_host=_config_secret(app_config, "gcsEmulatorHost"),
        gemini_api_key=_config_secret(app_config, "geminiApiKey"),
        openai_api_key=_config_secret(app_config, "openaiApiKey"),
        google_client_id=_config_secret(app_config, "googleClientId"),
        pangea_service_url=_config_secret(app_config, "pangeaServiceUrl"),
        jwt_secret_key=_config_secret(app_config, "jwtSecretKey"),
        jwt_algorithm=_config_secret(app_config, "jwtAlgorithm"),
        jwt_access_token_expiration_seconds=_config_secret(
            app_config,
            "jwtAccessTokenExpirationSeconds",
        ),
        jwt_refresh_token_expiration_seconds=_config_secret(
            app_config,
            "jwtRefreshTokenExpirationSeconds",
        ),
        resend_api_key=_config_secret(app_config, "resendApiKey"),
        resend_sender_email=_config_secret(app_config, "resendSenderEmail"),
        email_verification_secret_key=_config_secret(
            app_config,
            "emailVerificationSecretKey",
        ),
        email_verification_salt=_config_secret(app_config, "emailVerificationSalt"),
        email_verification_otp_ttl_seconds=_config_secret(
            app_config,
            "emailVerificationOtpTtlSeconds",
        ),
        email_verification_token_max_age_seconds=_config_secret(
            app_config,
            "emailVerificationTokenMaxAgeSeconds",
        ),
        api_image=app_config.get("apiImage")
        or "us-docker.pkg.dev/cloudrun/container/hello",
        mlflow_image=app_config.get("mlflowImage")
        or "us-docker.pkg.dev/cloudrun/container/hello",
        qdrant_url=_config_secret(app_config, "qdrantUrl"),
        qdrant_api_key=_config_secret(app_config, "qdrantApiKey"),
        inngest_event_key=_config_secret(app_config, "inngestEventKey"),
        inngest_signing_key=_config_secret(app_config, "inngestSigningKey"),
        onesignal_api_key=_config_secret(app_config, "onesignalApiKey"),
        supabase_storage_bucket=app_config.get("supabaseStorageBucket"),
        reset_password_otp_ttl_seconds=app_config.get(
            "resetPasswordOtpTtlSeconds"
        ),
        reset_password_otp_resend_cooldown_seconds=app_config.get(
            "resetPasswordOtpResendCooldownSeconds"
        ),
        reset_password_context_ttl_seconds=app_config.get(
            "resetPasswordContextTtlSeconds"
        ),
        supabase_url=app_config.get("supabaseUrl"),
        supabase_key=_config_secret(app_config, "supabaseKey"),
        onesignal_app_id=app_config.get("onesignalAppId"),
        onesignal_rest_api_key=_config_secret(app_config, "onesignalRestApiKey"),
        iam_user_email=app_config.get("iamUserEmail"),
        github_repository=app_config.get("githubRepository"),
        github_branch=app_config.get("githubBranch"),
    )
