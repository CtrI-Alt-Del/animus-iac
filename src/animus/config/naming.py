def resource_name(name: str, stack: str) -> str:
    return f"animus-{stack}-{name}" if name else f"animus-{stack}"


def service_account_id(name: str, stack: str) -> str:
    return f"animus-{stack}-{name}"[:30]


def secret_resource_id(name: str, environment: str) -> str:
    return f"{environment}-{name}".replace("_", "-")
