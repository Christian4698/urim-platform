from app.db.isolation import validate_isolated_test_database


def _validate(
    test_url: str | None,
    *,
    database_url: str | None = None,
    app_env: str = "test",
):
    return validate_isolated_test_database(
        test_url,
        database_url=database_url,
        app_env=app_env,
    )


def test_isolated_postgresql_test_database_is_accepted() -> None:
    result = _validate(
        "postgresql+psycopg://user:placeholder@db-test.internal/urim_test"  # pragma: allowlist secret
    )

    assert result.safe is True
    assert result.reason == "ISOLATED_TEST_DATABASE_CONFIRMED"


def test_missing_test_database_is_refused() -> None:
    assert _validate(None).reason == "B1_TEST_DATABASE_URL_MISSING"


def test_production_app_environment_is_refused() -> None:
    result = _validate(
        "postgresql://user:placeholder@db-test.internal/urim_test",  # pragma: allowlist secret
        app_env="production",
    )

    assert result.safe is False
    assert result.reason == "APP_ENV_PRODUCTION_LIKE"

    regional_result = _validate(
        "postgresql://user:placeholder@db-test.internal/urim_test",  # pragma: allowlist secret
        app_env="prod-eu",
    )
    assert regional_result.safe is False
    assert regional_result.reason == "APP_ENV_PRODUCTION_LIKE"


def test_exact_database_url_match_is_refused() -> None:
    url = "postgresql://user:placeholder@db-test.internal/urim_test"  # pragma: allowlist secret

    result = _validate(url, database_url=url)

    assert result.safe is False
    assert result.reason == "MATCHES_DATABASE_URL"


def test_same_target_with_different_credentials_is_refused() -> None:
    result = _validate(
        "postgresql://test_user:placeholder@db-test.internal:5432/urim_test",  # pragma: allowlist secret
        database_url=(
            "postgresql://app_user:placeholder2@db-test.internal/urim_test"  # pragma: allowlist secret
        ),
    )

    assert result.safe is False
    assert result.reason == "MATCHES_DATABASE_URL_TARGET"


def test_non_postgresql_and_ambiguous_targets_are_refused() -> None:
    sqlite_result = _validate("sqlite:///urim_test.db")
    ambiguous_result = _validate(
        "postgresql://user:placeholder@private.internal/urim"  # pragma: allowlist secret
    )

    assert sqlite_result.safe is False
    assert ambiguous_result.safe is False
    assert ambiguous_result.reason == (
        "B1_TEST_DATABASE_URL_NOT_EXPLICITLY_ISOLATED"
    )


def test_production_like_target_name_is_refused_even_with_test_marker() -> None:
    result = _validate(
        "postgresql://user:placeholder@prod-test.internal/urim_test"  # pragma: allowlist secret
    )

    assert result.safe is False
    assert result.reason == "B1_TEST_DATABASE_URL_PRODUCTION_LIKE"
