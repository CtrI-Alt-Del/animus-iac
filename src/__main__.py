import pulumi

from animus.config import load_settings
from animus.gcp import deploy as deploy_gcp
from animus.qdrant import deploy as deploy_qdrant


settings = load_settings()
qdrant = deploy_qdrant(settings)
gcp = deploy_gcp(settings, qdrant)

pulumi.export("stack", settings.stack)
pulumi.export("environment", settings.environment)
pulumi.export("gcp_project", settings.gcp_project)
pulumi.export("gcp_region", settings.gcp_region)
pulumi.export("is_production", settings.is_production)
pulumi.export("resource_prefix", settings.resource_prefix)
pulumi.export("secret_prefix", settings.secret_prefix)
pulumi.export("qdrant_collection_prefix", settings.qdrant_collection_prefix)
pulumi.export("qdrant_url", qdrant["cluster"]["url"])
pulumi.export("gcp", gcp)
pulumi.export("qdrant", qdrant)
