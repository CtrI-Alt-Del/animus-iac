import pulumi


config = pulumi.Config("gcp")
project = config.require("project")
region = config.require("region")
stack = pulumi.get_stack()

pulumi.export("stack", stack)
pulumi.export("gcp_project", project)
pulumi.export("gcp_region", region)
pulumi.export("is_production", stack == "prod")
