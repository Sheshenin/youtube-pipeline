from __future__ import annotations

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from pipeline.config import DEFAULT_DAYS, DEFAULT_LANGUAGE, DEFAULT_MIN_RESULTS, DEFAULT_REGION
from pipeline.run import run_pipeline

app = FastAPI()
app.mount("/static", StaticFiles(directory="webapp/static"), name="static")

templates = Jinja2Templates(directory="webapp/templates")


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    context = {
        "request": request,
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
) -> HTMLResponse:
    error = None
    result = None
    try:
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
        "defaults": {
            "topic": topic,
            "language": language,
            "region": region,
            "days": days,
            "min_results": min_results,
        },
        "result": result,
        "error": error,
    }
    return templates.TemplateResponse("index.html", context)
