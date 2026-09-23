"""Contract v1 HTTP routes over one immutable calculated snapshot."""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path
from time import monotonic
from typing import Any

from fastapi import FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from agent import investigate
from agent.session import SnapshotMismatch
from pipeline.run import CSV_COLUMNS, DEFAULT_OUT

from .service import EntityNotFound, InvestigatorProvider, SnapshotService

logger = logging.getLogger("uvicorn.error")


def _error(code: str, message: str, status: int) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})


def create_app(*, snapshot_path: Path | None = None, service: SnapshotService | None = None,
               model: Any = None, static_dir: Path | None = None,
               auto_model: bool = False) -> FastAPI:
    app = FastAPI(title="HackAlem API", version="1")
    path = snapshot_path or DEFAULT_OUT / "snapshot.json"
    if service is None and path.is_file():
        service = SnapshotService.from_file(path)
    app.state.service = service
    app.state.export_dir = path.parent
    app.state.model = model
    app.state.auto_model = auto_model

    @app.exception_handler(RequestValidationError)
    async def invalid_request(_request: Request, _exc: RequestValidationError) -> JSONResponse:
        return _error("INVALID_REQUEST", "Некорректные параметры запроса.", 422)

    @app.exception_handler(ValueError)
    async def invalid_value(_request: Request, error: ValueError) -> JSONResponse:
        return _error("INVALID_REQUEST", str(error), 422)

    @app.exception_handler(EntityNotFound)
    async def missing_entity(_request: Request, error: EntityNotFound) -> JSONResponse:
        return _error("ENTITY_NOT_FOUND", f"gid {error.args[0]} не найден.", 404)

    @app.exception_handler(LookupError)
    async def missing_agent_entity(_request: Request, error: LookupError) -> JSONResponse:
        return _error("ENTITY_NOT_FOUND", str(error), 404)

    @app.exception_handler(SnapshotMismatch)
    async def stale_snapshot(_request: Request, _error_value: SnapshotMismatch) -> JSONResponse:
        return _error("SNAPSHOT_MISMATCH", "Snapshot изменился; обновите данные.", 409)

    def current() -> SnapshotService:
        if app.state.service is None:
            raise FileNotFoundError("snapshot not ready")
        return app.state.service

    @app.exception_handler(FileNotFoundError)
    async def no_snapshot(_request: Request, _error_value: FileNotFoundError) -> JSONResponse:
        return _error("SNAPSHOT_NOT_READY", "Сначала запустите pipeline.", 503)

    @app.get("/api/summary")
    def summary() -> dict:
        return current().summary()

    @app.get("/api/entities")
    def entities(role: str | None = None, cluster_id: int | None = Query(default=None, ge=0),
                 is_seed: str | None = None, offset: int = Query(default=0, ge=0),
                 limit: int = Query(default=20, ge=1, le=200)) -> dict:
        if is_seed not in (None, "true", "false"):
            raise ValueError("is_seed must be true or false")
        return current().list_entities(role=role, cluster_id=cluster_id,
                                       is_seed=None if is_seed is None else is_seed == "true",
                                       offset=offset, limit=limit)

    @app.get("/api/entities/{gid}")
    def entity(gid: str) -> dict:
        return current().get_entity(gid)

    @app.get("/api/subgraph")
    def subgraph(gid: str, hops: int = Query(default=1, ge=1, le=2),
                 limit: int = Query(default=80, ge=1, le=200)) -> dict:
        return current().get_subgraph(gid, hops, limit)

    @app.get("/api/clusters")
    def clusters() -> dict:
        return current().clusters()

    @app.get("/api/export/{filename}")
    def export(filename: str):
        current()
        if filename not in CSV_COLUMNS:
            raise ValueError("unsupported export filename")
        target = app.state.export_dir / filename
        if not target.is_file():
            raise FileNotFoundError(filename)
        return FileResponse(target, media_type="text/csv; charset=utf-8", filename=filename)

    @app.post("/api/investigate")
    async def investigation(request: dict) -> dict:
        snapshot = current()
        started = monotonic()
        selected = request.get("selected_gids")
        logger.info("investigation received snapshot=%s selected_count=%s",
                    snapshot.meta["snapshot_id"], len(selected) if isinstance(selected, list) else "invalid")
        selected_model = app.state.model
        managed_client = None
        if app.state.auto_model and selected_model is None and os.getenv("OPENAI_API_KEY", "").strip():
            try:
                from openai import AsyncOpenAI
                from .openai_model import OpenAIInvestigatorModel

                managed_client = AsyncOpenAI(
                    api_key=os.environ["OPENAI_API_KEY"].strip(), timeout=25.0, max_retries=0,
                )
                selected_model = OpenAIInvestigatorModel(
                    managed_client, model_name=os.getenv("OPENAI_MODEL", "gpt-5.4-mini").strip()
                    or "gpt-5.4-mini",
                )
            except Exception:
                logger.exception("investigation model initialization failed")
        try:
            result = await investigate(
                request, InvestigatorProvider(snapshot), selected_model,
                meta=snapshot.meta, known_gids=snapshot.known_gids,
            )
            logger.info("investigation completed status=%s duration_ms=%d tools=%s",
                        result["status"], int((monotonic() - started) * 1000),
                        [(call["name"], call["status"]) for call in result["tool_calls"]])
            return result
        finally:
            if managed_client is not None:
                try:
                    await asyncio.wait_for(managed_client.close(), timeout=2.0)
                except Exception:
                    logger.exception("investigation model client close failed")

    site = static_dir or Path(__file__).resolve().parents[1] / "frontend" / "dist"
    if site.is_dir():
        app.mount("/", StaticFiles(directory=site, html=True), name="frontend")
    return app


app = create_app(auto_model=True)
