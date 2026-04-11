from animus.config import Settings


def build_cluster_config(settings: Settings) -> dict[str, object]:
    return {
        "provider": "qdrant-cloud",
        "shared_across_environments": True,
        "secret_prefix": settings.secret_prefix,
        "url": settings.qdrant_url,
        "api_key": settings.qdrant_api_key,
    }
