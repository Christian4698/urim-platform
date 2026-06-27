from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.core.config import settings
from app.core.constants import API_PHASE, READ_ONLY_SKELETON


class ApiMetadata(BaseModel):
    app_name: str
    engine_name: str
    locale: str
    currency: str
    phase: str

    model_config = ConfigDict(extra="forbid")


class Pagination(BaseModel):
    limit: int = 0
    offset: int = 0
    total: int = 0

    model_config = ConfigDict(extra="forbid")


class StandardError(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")


class StandardResponse(BaseModel):
    metadata: ApiMetadata
    status: str
    data: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")


class SkeletonCollectionResponse(BaseModel):
    metadata: ApiMetadata
    resource: str
    status: str = READ_ONLY_SKELETON
    items: list[dict[str, Any]] = Field(default_factory=list)
    pagination: Pagination = Field(default_factory=Pagination)
    safeguards: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


def build_metadata() -> ApiMetadata:
    return ApiMetadata(
        app_name=settings.app_name,
        engine_name=settings.engine_name,
        locale=settings.default_locale,
        currency=settings.default_currency,
        phase=API_PHASE,
    )


def empty_collection(resource: str, safeguards: list[str]) -> SkeletonCollectionResponse:
    return SkeletonCollectionResponse(
        metadata=build_metadata(),
        resource=resource,
        safeguards=safeguards,
    )
