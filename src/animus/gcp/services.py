import pulumi_gcp as gcp

from animus.config import Settings


_REQUIRED_SERVICES = [
    "artifactregistry.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "compute.googleapis.com",
    "iam.googleapis.com",
    "redis.googleapis.com",
    "run.googleapis.com",
    "servicenetworking.googleapis.com",
    "sqladmin.googleapis.com",
    "storage.googleapis.com",
    "vpcaccess.googleapis.com",
]


def enable_services(settings: Settings) -> dict[str, object]:
    resources = []
    names = []

    for service in _REQUIRED_SERVICES:
        resource = gcp.projects.Service(
            service.replace(".", "-").replace("googleapis-com", "api"),
            project=settings.gcp_project,
            service=service,
            disable_on_destroy=False,
        )
        resources.append(resource)
        names.append(resource.service)

    return {
        "enabled": names,
        "_resources": resources,
    }
