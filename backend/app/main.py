from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.api.v1.router import api_router
from app.core.exceptions import (
    AuthenticationError,
    ConflictError,
    NotFoundError,
    UnprocessableError,
)
from app.core.logging import CorrelationIdMiddleware, configure_logging
from app.integrations.squad.exceptions import SquadAPIError


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title="Insureflow")
    app.add_middleware(CorrelationIdMiddleware)
    app.include_router(api_router, prefix="/api/v1")

    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(ConflictError)
    async def conflict_handler(request: Request, exc: ConflictError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(AuthenticationError)
    async def authentication_error_handler(
        request: Request, exc: AuthenticationError
    ) -> JSONResponse:
        return JSONResponse(status_code=401, content={"detail": str(exc)})

    @app.exception_handler(UnprocessableError)
    async def unprocessable_error_handler(
        request: Request, exc: UnprocessableError
    ) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(SquadAPIError)
    async def squad_api_error_handler(request: Request, exc: SquadAPIError) -> JSONResponse:
        return JSONResponse(
            status_code=502,
            content={"detail": f"Squad API error: {exc}", "squad_status_code": exc.status_code},
        )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/metrics")
    async def metrics() -> Response:
        # Unauthenticated, matching standard Prometheus scrape conventions
        # (the scraper carries no app JWT) -- a real deploy restricts network
        # access to this path at the ingress/security-group level, same
        # posture as any other infra-only endpoint.
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return app


app = create_app()
