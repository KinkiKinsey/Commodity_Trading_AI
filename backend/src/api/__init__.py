from __future__ import annotations

import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .pricing import router as pricing_router
from .news import router as news_router
from .oil_factors import router as oil_factors_router
from .ctp import router as ctp_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Ringshell Pricing API",
        version="0.1.0",
        description="K-line and technical indicator endpoints for the Ringshell platform.",
    )

    raw_origins = os.getenv(
        "CORS_ALLOW_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    )
    allowed_origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
    if not allowed_origins:
        allowed_origins = ["*"]

    allow_origin_regex_env = os.getenv("CORS_ALLOW_ORIGIN_REGEX")
    allow_origin_regex = allow_origin_regex_env if allow_origin_regex_env else None

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_origin_regex=allow_origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(pricing_router)
    app.include_router(news_router)
    app.include_router(oil_factors_router)
    app.include_router(ctp_router)
    return app


app = create_app()


@app.get("/healthz", summary="Health probe")
async def health_probe() -> dict[str, str]:
    return {"status": "ok"}
