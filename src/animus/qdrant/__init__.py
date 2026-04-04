from .cluster import build_cluster_config
from .collections import build_collections_config
from animus.config import Settings


def deploy(settings: Settings) -> dict[str, object]:
    cluster = build_cluster_config(settings)
    collections = build_collections_config(settings)
    return {
        "cluster": cluster,
        "collections": collections,
    }
