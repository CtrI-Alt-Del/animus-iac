import pulumi
import pulumi_gcp as gcp

from animus.config import Settings, service_account_id


def _github_attribute_condition(settings: Settings) -> str:
    condition = f"assertion.repository == '{settings.github_repository}'"
    if settings.github_branch:
        condition = (
            f"{condition} && assertion.ref == 'refs/heads/{settings.github_branch}'"
        )
    return condition


def build_identity_config(
    settings: Settings,
    project_services: dict[str, object],
    secrets: dict[str, object],
) -> dict[str, object]:
    dependencies = project_services["_resources"]

    runtime = gcp.serviceaccount.Account(
        "runtime-service-account",
        account_id=service_account_id("run", settings.stack),
        display_name=f"Animus {settings.stack} runtime",
        project=settings.gcp_project,
        opts=pulumi.ResourceOptions(depends_on=dependencies),
    )

    deploy = gcp.serviceaccount.Account(
        "deploy-service-account",
        account_id=service_account_id("deploy", settings.stack),
        display_name=f"Animus {settings.stack} deploy",
        project=settings.gcp_project,
        opts=pulumi.ResourceOptions(depends_on=dependencies),
    )

    runtime_roles = [
        "roles/cloudsql.client",
        "roles/storage.objectAdmin",
    ]
    for index, role in enumerate(runtime_roles):
        gcp.projects.IAMMember(
            f"runtime-project-role-{index}",
            project=settings.gcp_project,
            role=role,
            member=runtime.member,
            opts=pulumi.ResourceOptions(depends_on=[runtime]),
        )

    deploy_roles = [
        "roles/artifactregistry.admin",
        "roles/cloudsql.admin",
        "roles/iam.serviceAccountUser",
        "roles/redis.admin",
        "roles/run.admin",
        "roles/secretmanager.admin",
        "roles/serviceusage.serviceUsageAdmin",
        "roles/storage.admin",
        "roles/vpcaccess.admin",
    ]
    for index, role in enumerate(deploy_roles):
        gcp.projects.IAMMember(
            f"deploy-project-role-{index}",
            project=settings.gcp_project,
            role=role,
            member=deploy.member,
            opts=pulumi.ResourceOptions(depends_on=[deploy]),
        )

    for name, secret in secrets["_secret_resources"].items():
        gcp.secretmanager.SecretIamMember(
            f"{name}-secret-accessor",
            project=settings.gcp_project,
            secret_id=secret.id,
            role="roles/secretmanager.secretAccessor",
            member=runtime.member,
            opts=pulumi.ResourceOptions(depends_on=[runtime, secret]),
        )

    workload_identity = None
    if settings.github_repository:
        pool = gcp.iam.WorkloadIdentityPool(
            "github-workload-identity-pool",
            project=settings.gcp_project,
            workload_identity_pool_id=f"animus-{settings.stack}-github",
            display_name=f"Animus {settings.stack} GitHub",
            opts=pulumi.ResourceOptions(depends_on=dependencies),
        )

        provider = gcp.iam.WorkloadIdentityPoolProvider(
            "github-workload-identity-provider",
            project=settings.gcp_project,
            workload_identity_pool_id=pool.workload_identity_pool_id,
            workload_identity_pool_provider_id="github-oidc",
            display_name="GitHub Actions",
            attribute_mapping={
                "google.subject": "assertion.sub",
                "attribute.actor": "assertion.actor",
                "attribute.ref": "assertion.ref",
                "attribute.repository": "assertion.repository",
            },
            attribute_condition=_github_attribute_condition(settings),
            oidc={
                "issuer_uri": "https://token.actions.githubusercontent.com",
            },
            opts=pulumi.ResourceOptions(depends_on=[pool]),
        )

        github_member = pulumi.Output.concat(
            "principalSet://iam.googleapis.com/",
            pool.name,
            f"/attribute.repository/{settings.github_repository}",
        )

        gcp.serviceaccount.IAMMember(
            "github-workload-identity-user",
            service_account_id=deploy.name,
            role="roles/iam.workloadIdentityUser",
            member=github_member,
            opts=pulumi.ResourceOptions(depends_on=[deploy, provider]),
        )

        workload_identity = {
            "pool_name": pool.name,
            "provider_name": provider.name,
            "github_repository": settings.github_repository,
        }

    return {
        "runtime_service_account_email": runtime.email,
        "runtime_service_account_member": runtime.member,
        "deploy_service_account_email": deploy.email,
        "deploy_service_account_member": deploy.member,
        "workload_identity": workload_identity,
    }
