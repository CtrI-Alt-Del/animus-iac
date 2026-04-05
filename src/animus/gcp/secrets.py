import pulumi

from animus.config import Settings


ENV_SECRET_NAMES = (
    "MODE",
    "POSTGRES_PASSWORD",
    "DATABASE_URL",
    "GCS_EMULATOR_HOST",
    "GEMINI_API_KEY",
    "OPENAI_API_KEY",
    "GOOGLE_CLIENT_ID",
    "PANGEA_SERVICE_URL",
    "QDRANT_URL",
    "QDRANT_API_KEY",
    "INNGEST_EVENT_KEY",
    "INNGEST_SIGNING_KEY",
    "JWT_SECRET_KEY",
    "JWT_ALGORITHM",
    "JWT_ACCESS_TOKEN_EXPIRATION_SECONDS",
    "JWT_REFRESH_TOKEN_EXPIRATION_SECONDS",
    "EMAIL_VERIFICATION_OTP_TTL_SECONDS",
    "RESEND_API_KEY",
    "RESEND_SENDER_EMAIL",
    "EMAIL_VERIFICATION_SECRET_KEY",
    "EMAIL_VERIFICATION_SALT",
    "EMAIL_VERIFICATION_TOKEN_MAX_AGE_SECONDS",
)

def build_secrets_config(
    settings: Settings,
    project_services: dict[str, object],
) -> dict[str, object]:
    _ = project_services

    secret_specs: dict[str, pulumi.Input[str] | None] = {
        name.lower().replace("_", "-"): None for name in ENV_SECRET_NAMES
    }

    secret_specs["postgres-password"] = settings.database_password

    if settings.database_url is not None:
        secret_specs["database-url"] = settings.database_url

    if settings.gcs_emulator_host is not None:
        secret_specs["gcs-emulator-host"] = settings.gcs_emulator_host

    if settings.gemini_api_key is not None:
        secret_specs["gemini-api-key"] = settings.gemini_api_key

    if settings.openai_api_key is not None:
        secret_specs["openai-api-key"] = settings.openai_api_key

    if settings.google_client_id is not None:
        secret_specs["google-client-id"] = settings.google_client_id

    if settings.pangea_service_url is not None:
        secret_specs["pangea-service-url"] = settings.pangea_service_url

    if settings.qdrant_url is not None:
        secret_specs["qdrant-url"] = settings.qdrant_url

    if settings.qdrant_api_key is not None:
        secret_specs["qdrant-api-key"] = settings.qdrant_api_key

    if settings.inngest_event_key is not None:
        secret_specs["inngest-event-key"] = settings.inngest_event_key

    if settings.inngest_signing_key is not None:
        secret_specs["inngest-signing-key"] = settings.inngest_signing_key

    if settings.jwt_secret_key is not None:
        secret_specs["jwt-secret-key"] = settings.jwt_secret_key

    if settings.jwt_algorithm is not None:
        secret_specs["jwt-algorithm"] = settings.jwt_algorithm

    if settings.jwt_access_token_expiration_seconds is not None:
        secret_specs["jwt-access-token-expiration-seconds"] = (
            settings.jwt_access_token_expiration_seconds
        )

    if settings.jwt_refresh_token_expiration_seconds is not None:
        secret_specs["jwt-refresh-token-expiration-seconds"] = (
            settings.jwt_refresh_token_expiration_seconds
        )

    if settings.resend_api_key is not None:
        secret_specs["resend-api-key"] = settings.resend_api_key

    if settings.resend_sender_email is not None:
        secret_specs["resend-sender-email"] = settings.resend_sender_email

    if settings.email_verification_secret_key is not None:
        secret_specs["email-verification-secret-key"] = (
            settings.email_verification_secret_key
        )

    if settings.email_verification_salt is not None:
        secret_specs["email-verification-salt"] = settings.email_verification_salt

    if settings.email_verification_otp_ttl_seconds is not None:
        secret_specs["email-verification-otp-ttl-seconds"] = (
            settings.email_verification_otp_ttl_seconds
        )

    if settings.email_verification_token_max_age_seconds is not None:
        secret_specs["email-verification-token-max-age-seconds"] = (
            settings.email_verification_token_max_age_seconds
        )

    if settings.onesignal_api_key is not None:
        secret_specs["onesignal-api-key"] = settings.onesignal_api_key

    rendered = {}

    for name, value in secret_specs.items():
        rendered[name] = {
            "logical_name": f"{settings.secret_prefix}{name.replace('-', '_')}",
            "has_value": value is not None,
            "value": value,
        }

    return {
        "prefix": settings.secret_prefix,
        "manager": "pulumi-config-secrets",
        "single_source_of_truth": True,
        "items": rendered,
    }
