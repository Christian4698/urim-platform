from fastapi import FastAPI

from app.api.v1.routes import fixtures, post_match, predictions, providers, system, tickets

API_V1_ROUTERS = (
    system.router,
    fixtures.router,
    predictions.router,
    tickets.router,
    providers.router,
    post_match.router,
)


def include_api_v1(app: FastAPI) -> None:
    for router in API_V1_ROUTERS:
        app.include_router(router, prefix="/api/v1")
