import pulumi
import pulumi_gcp as gcp

from animus.config import Settings, resource_name


def build_artifact_registry_config(
    settings: Settings,
    project_services: dict[str, object],
) -> dict[str, object]:
    repository = gcp.artifactregistry.Repository(
        "artifact-registry-repository",
        repository_id=resource_name("docker", settings.stack),
        format="DOCKER",
        location=settings.gcp_region,
        description=f"Docker images for Animus {settings.stack}",
        project=settings.gcp_project,
        opts=pulumi.ResourceOptions(depends_on=project_services["_resources"]),
    )

    repository_url = pulumi.Output.concat(
        settings.gcp_region,
        "-docker.pkg.dev/",
        settings.gcp_project,
        "/",
        repository.repository_id,
    )

    return {
        "repository_id": repository.repository_id,
        "format": repository.format,
        "location": repository.location,
        "repository_name": repository.name,
        "repository_url": repository_url,
    }
