from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.constants import PHASE_LIVE_ENABLED, PHASE_REAL_BETTING_ENABLED
from app.core.cors import normalize_cors_origins

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'",
}


def add_cors(app: FastAPI, allowed_origins: tuple[str, ...]) -> None:
    exact_origins = normalize_cors_origins(allowed_origins)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(exact_origins),
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["Accept", "Content-Type"],
        max_age=600,
    )


def add_security_headers(app: FastAPI) -> None:
    @app.middleware("http")
    async def security_headers_middleware(request, call_next):
        response = await call_next(request)
        for header_name, header_value in SECURITY_HEADERS.items():
            if header_name not in response.headers:
                response.headers[header_name] = header_value
        return response


def phase_fourteen_security_assertions() -> dict[str, bool]:
    """Expose non-secret safety switches for smoke tests and future gates."""
    return {
        "providers_disabled": True,
        "bookmakers_disabled": True,
        "ml_disabled": True,
        "live_disabled": not PHASE_LIVE_ENABLED,
        "real_betting_disabled": not PHASE_REAL_BETTING_ENABLED,
        "prediction_creation_disabled": True,
        "production_mocks_disabled": True,
    }
