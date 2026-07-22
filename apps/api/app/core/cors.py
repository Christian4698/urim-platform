from urllib.parse import urlsplit


def normalize_cors_origins(value: str | tuple[str, ...]) -> tuple[str, ...]:
    """Return validated, exact HTTP(S) origins for the public browser client."""
    raw_origins = value.split(",") if isinstance(value, str) else value
    normalized: list[str] = []

    for raw_origin in raw_origins:
        origin = raw_origin.strip()
        if not origin:
            continue
        if "*" in origin:
            raise ValueError("Wildcard CORS origins are not allowed.")

        parsed = urlsplit(origin)
        try:
            port = parsed.port
        except ValueError as error:
            raise ValueError("CORS origins must use a valid port.") from error

        if (
            parsed.scheme.lower() not in {"http", "https"}
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.path not in {"", "/"}
            or parsed.query
            or parsed.fragment
            or any(character.isspace() for character in origin)
        ):
            raise ValueError("CORS origins must be exact HTTP(S) origins.")

        hostname = parsed.hostname.lower()
        if ":" in hostname:
            hostname = f"[{hostname}]"
        host = f"{hostname}:{port}" if port is not None else hostname
        exact_origin = f"{parsed.scheme.lower()}://{host}"
        if exact_origin not in normalized:
            normalized.append(exact_origin)

    if not normalized:
        raise ValueError("At least one exact CORS origin is required.")

    return tuple(normalized)
