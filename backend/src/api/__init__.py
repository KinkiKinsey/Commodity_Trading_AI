from __future__ import annotations

from fastapi import FastAPI

from .pricing import router as pricing_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Ringshell Pricing API",
        version="0.1.0",
        description="K-line and technical indicator endpoints for the Ringshell platform.",
    )
    app.include_router(pricing_router)
    return app


app = create_app()


@app.get("/healthz", summary="Health probe")
async def health_probe() -> dict[str, str]:
    return {"status": "ok"}
