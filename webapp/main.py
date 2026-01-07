from __future__ import annotations

import json

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from pipeline.config import (
    DEFAULT_DAYS,
    DEFAULT_LANGUAGE,
    DEFAULT_MIN_RESULTS,
    DEFAULT_REGION,
    VERSION,
)
from pipeline.run import collect_shorts, enrich_results, run_pipeline
from services.query_expander import expand_queries
from services.sheets import write_rows

app = FastAPI()
app.mount("/static", StaticFiles(directory="webapp/static"), name="static")

templates = Jinja2Templates(directory="webapp/templates")


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    context = {
        "request": request,
        "version": VERSION,
        "defaults": {
            "topic": "",
            "language": DEFAULT_LANGUAGE,
            "region": DEFAULT_REGION,
            "days": DEFAULT_DAYS,
            "min_results": DEFAULT_MIN_RESULTS,
        },
        "result": None,
        "error": None,
    }
    return templates.TemplateResponse("index.html", context)


@app.post("/run", response_class=HTMLResponse)
def run(
    request: Request,
    topic: str = Form(...),
    language: str = Form(DEFAULT_LANGUAGE),
    region: str = Form(DEFAULT_REGION),
    days: int = Form(DEFAULT_DAYS),
    min_results: int = Form(DEFAULT_MIN_RESULTS),
    checkpoint: str = Form("start"),
    serialized_results: str | None = Form(None),
    query_count: int | None = Form(None),
) -> HTMLResponse:
    error = None
    result = None
    checkpoint_state: str | None = None
    queries: list[str] | None = None
    saved_links: list[str] | None = None

    try:
        # CHECKPOINT_MARKER: show prepared queries before search
        if checkpoint == "start":
            queries = expand_queries(topic, language=language)
            checkpoint_state = "queries"
        # CHECKPOINT_MARKER: list filtered shorts before enrichment
        elif checkpoint == "confirm_queries":
            collection = collect_shorts(
                topic=topic,
                language=language,
                region=region,
                days=days,
                min_results=min_results,
            )
            queries = collection["queries"]
            saved_links = [
                video.get("url") for video in collection["results"] if video.get("url")
            ]
            serialized_results = json.dumps(collection["results"])
            query_count = len(collection["queries"])
            checkpoint_state = "shorts"
        else:
            # CHECKPOINT_MARKER: finish pipeline after confirmations
            results_payload = []
            if serialized_results:
                try:
                    results_payload = json.loads(serialized_results)
                except json.JSONDecodeError:
                    results_payload = []

            if results_payload:
                rows = enrich_results(results_payload)
                write_rows(rows)
                result = {
                    "topic": topic,
                    "query_count": query_count or len(results_payload),
                    "shorts_count": len(results_payload),
                    "rows_written": len(rows),
                }
            else:
                result = run_pipeline(
                    topic=topic,
                    language=language,
                    region=region,
                    days=days,
                    min_results=min_results,
                )
    except Exception as exc:  # noqa: BLE001
        error = str(exc)

    context = {
        "request": request,
        "version": VERSION,
        "defaults": {
            "topic": topic,
            "language": language,
            "region": region,
            "days": days,
            "min_results": min_results,
        },
        "checkpoint": checkpoint_state,
        "queries": queries,
        "saved_links": saved_links,
        "serialized_results": serialized_results,
        "query_count": query_count,
        "result": result,
        "error": error,
    }
    return templates.TemplateResponse("index.html", context)
