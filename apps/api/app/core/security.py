from app.core.config import settings


def phase_one_security_assertions() -> dict[str, bool]:
    """Expose non-secret safety switches for smoke tests and future gates."""
    return {
        "live_disabled": not settings.enable_live,
        "real_betting_disabled": not settings.enable_real_betting,
        "production_mocks_disabled": not settings.allow_production_mocks,
    }
