import pulumi
import pulumi_gcp as gcp

from animus.config import Settings, resource_name


def build_storage_config(
    settings: Settings,
    project_services: dict[str, object],
) -> dict[str, object]:
    bucket_name = f"{settings.gcp_project}-{resource_name('files', settings.stack)}"[
        :63
    ]

    bucket = gcp.storage.Bucket(
        "animus-bucket",
        name=bucket_name,
        project=settings.gcp_project,
        location=settings.gcp_region,
        uniform_bucket_level_access=True,
        versioning=gcp.storage.BucketVersioningArgs(
            enabled=settings.storage_versioning_enabled,
        ),
        opts=pulumi.ResourceOptions(depends_on=project_services["_resources"]),
    )

    return {
        "bucket_name": bucket.name,
        "location": bucket.location,
        "versioning_enabled": settings.storage_versioning_enabled,
        "url": bucket.url,
    }
