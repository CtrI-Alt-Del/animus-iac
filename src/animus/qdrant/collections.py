from animus.config import Settings


def build_collections_config(settings: Settings) -> dict[str, object]:
    return {
        "prefix": settings.qdrant_collection_prefix,
        "precedents_collection_name": f"{settings.qdrant_collection_prefix}precedents",
    }
