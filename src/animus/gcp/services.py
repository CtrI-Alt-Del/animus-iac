import pulumi
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
    service_resources = {}

    for service in _REQUIRED_SERVICES:
        resource = gcp.projects.Service(
            service.replace(".", "-").replace("googleapis-com", "api"),
            project=settings.gcp_project,
            service=service,
            disable_on_destroy=False,
        )
        resources.append(resource)
        names.append(resource.service)
        service_resources[service] = resource

    vpcaccess_service_identity = gcp.projects.ServiceIdentity(
        "vpcaccess-service-identity",
        project=settings.gcp_project,
        service="vpcaccess.googleapis.com",
        opts=pulumi.ResourceOptions(
            depends_on=[service_resources["vpcaccess.googleapis.com"]]
        ),
    )
    resources.append(vpcaccess_service_identity)

    vpcaccess_service_agent_role = gcp.projects.IAMMember(
        "vpcaccess-service-agent-role",
        project=settings.gcp_project,
        role="roles/vpcaccess.serviceAgent",
        member=vpcaccess_service_identity.member,
        opts=pulumi.ResourceOptions(depends_on=[vpcaccess_service_identity]),
    )
    resources.append(vpcaccess_service_agent_role)

    return {
        "enabled": names,
        "_resources": resources,
        "vpcaccess_service_identity_email": vpcaccess_service_identity.email,
    }
