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
from pipeline.run import attach_transcripts, collect_shorts, finalize_results, run_pipeline

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
) -> HTMLResponse:
    error = None
    result = None
    checkpoint_state: str | None = None
    transcript_items: list[dict] | None = None
    serialized_payload: str | None = serialized_results

    try:
        if checkpoint == "start":
            collection = collect_shorts(
                topic=topic,
                language=language,
                region=region,
                days=days,
                min_results=min_results,
            )
            results_with_transcripts = attach_transcripts(
                collection["results"],
                language=language,
            )
            transcript_items = results_with_transcripts
            serialized_payload = json.dumps(
                {"queries": collection["queries"], "results": results_with_transcripts}
            )
            checkpoint_state = "transcripts"
        elif checkpoint == "confirm_transcripts":
            payload = {}
            if serialized_results:
                payload = json.loads(serialized_results)
            queries = payload.get("queries") or []
            results_with_transcripts = payload.get("results") or []
            result = finalize_results(topic=topic, queries=queries, results=results_with_transcripts)
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
        "transcripts": transcript_items,
        "serialized_results": serialized_payload,
        "result": result,
        "error": error,
    }
    return templates.TemplateResponse("index.html", context)
