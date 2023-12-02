import validators  # type: ignore


def domain(instance, attribute, value):
    if (
        not validators.domain(value)
        and not validators.ipv4(value)
        and not validators.ipv6(value)
    ):
        raise ValueError(f"{value!r} is not a valid SIP domain")
