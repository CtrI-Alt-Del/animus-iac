import pulumi_gcp as gcp

import pulumi

from animus.config import Settings, resource_name


def _subnet_cidr_for_environment(environment: str) -> str:
    if environment == "prod":
        return "10.10.0.0/24"
    if environment == "stg":
        return "10.20.0.0/24"
    return "10.30.0.0/24"


def _connector_subnet_cidr_for_environment(environment: str) -> str:
    if environment == "prod":
        return "10.10.1.0/28"
    if environment == "stg":
        return "10.20.1.0/28"
    return "10.30.1.0/28"


def _vpc_connector_name(stack: str) -> str:
    # Serverless VPC Access connector names must be shorter than 21 chars,
    # and hyphens count twice for that limit.
    return f"ani-{stack}-vpca"


def build_network_config(
    settings: Settings,
    project_services: dict[str, object],
) -> dict[str, object]:
    network_name = resource_name("vpc", settings.stack)
    subnet_name = resource_name("subnet", settings.stack)
    connector_subnet_name = resource_name("connector-subnet", settings.stack)
    peering_range_name = resource_name("private-services", settings.stack)
    connector_name = _vpc_connector_name(settings.stack)

    network = gcp.compute.Network(
        "network",
        name=network_name,
        auto_create_subnetworks=False,
        routing_mode="REGIONAL",
        opts=pulumi.ResourceOptions(depends_on=project_services["_resources"]),
    )

    subnetwork = gcp.compute.Subnetwork(
        "network-subnet",
        name=subnet_name,
        region=settings.gcp_region,
        ip_cidr_range=_subnet_cidr_for_environment(settings.environment),
        network=network.id,
        private_ip_google_access=True,
    )

    connector_subnetwork = gcp.compute.Subnetwork(
        "network-connector-subnet",
        name=connector_subnet_name,
        region=settings.gcp_region,
        ip_cidr_range=_connector_subnet_cidr_for_environment(settings.environment),
        network=network.id,
        private_ip_google_access=True,
    )

    private_services_range = gcp.compute.GlobalAddress(
        "network-private-services-range",
        name=peering_range_name,
        purpose="VPC_PEERING",
        address_type="INTERNAL",
        prefix_length=16,
        network=network.id,
    )

    private_services_connection = gcp.servicenetworking.Connection(
        "network-private-services-connection",
        network=network.id,
        service="servicenetworking.googleapis.com",
        reserved_peering_ranges=[private_services_range.name],
        deletion_policy="ABANDON",
    )

    vpc_connector = gcp.vpcaccess.Connector(
        "network-vpc-access-connector",
        name=connector_name,
        region=settings.gcp_region,
        subnet={"name": connector_subnetwork.name},
        machine_type="e2-micro",
        min_instances=2,
        max_instances=3,
        opts=pulumi.ResourceOptions(depends_on=[connector_subnetwork]),
    )

    return {
        "name": network.name,
        "id": network.id,
        "self_link": network.self_link,
        "region": settings.gcp_region,
        "subnetwork_name": subnetwork.name,
        "subnetwork_id": subnetwork.id,
        "subnetwork_cidr": subnetwork.ip_cidr_range,
        "connector_subnetwork_name": connector_subnetwork.name,
        "connector_subnetwork_id": connector_subnetwork.id,
        "connector_subnetwork_cidr": connector_subnetwork.ip_cidr_range,
        "private_services_access": True,
        "private_services_range_name": private_services_range.name,
        "private_services_connection": private_services_connection.peering,
        "vpc_connector_name": vpc_connector.name,
        "vpc_connector_id": vpc_connector.id,
        "_private_services_connection_resource": private_services_connection,
    }
