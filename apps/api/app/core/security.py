from fastapi import FastAPI

from app.core.config import settings

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
}


def add_security_headers(app: FastAPI) -> None:
    @app.middleware("http")
    async def security_headers_middleware(request, call_next):
        response = await call_next(request)
        for header_name, header_value in SECURITY_HEADERS.items():
            if header_name not in response.headers:
                response.headers[header_name] = header_value
        return response


def phase_three_security_assertions() -> dict[str, bool]:
    """Expose non-secret safety switches for smoke tests and future gates."""
    return {
        "providers_disabled": True,
        "bookmakers_disabled": True,
        "ml_disabled": True,
        "live_disabled": not settings.enable_live,
        "real_betting_disabled": not settings.enable_real_betting,
        "prediction_creation_disabled": True,
        "production_mocks_disabled": not settings.allow_production_mocks,
    }


phase_two_security_assertions = phase_three_security_assertions
phase_one_security_assertions = phase_two_security_assertions
