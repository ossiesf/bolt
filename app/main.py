import asyncio
import csv
import os
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException, Response, Request
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from prometheus_client import generate_latest, make_asgi_app, CONTENT_TYPE_LATEST

from app.database import Base, Session, engine, Click
from app.middleware.metrics import MetricsMiddleware
from app.models import ShortenRequest, ShortenResponse
from app.routes import Routes, get_db
from app.shortener import create_short_code


routes = Routes()
app = FastAPI()
app.add_middleware(MetricsMiddleware)
app.mount("/static", StaticFiles(directory="web"), name="static")

# Mount prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

@app.on_event("startup")
def startup():
    # Create tables
    Base.metadata.create_all(bind=engine)
    
# Serve the web UI at root and allow HEAD requests for Uptime Robot
@app.get("/")
@app.head("/")
async def read_root():
    return FileResponse("web/shortener.html")

# Serve the load test page
@app.get("/load-test.html")
def load_test_page():
    return FileResponse("web/load-test.html")

# Routes are in order, if health is after /{short_code} it will never be reached
@app.get("/health")
def health_check():
    return {"status": "healthy"}

class LoadTestRequest(BaseModel):
    users: int = 10
    duration: int = 30

load_test_lock = asyncio.Lock()
@app.post("/api/run-load-test")
async def run_load_test(request: LoadTestRequest):
    try:
        # Check if asyncio is locked
        if load_test_lock.locked():
            return {"status": "busy", "message": "A load test is already running, try again later"}
        
        async with load_test_lock:
            # Use asyncio subprocess - non-blocking
            process = await asyncio.create_subprocess_exec(
                "locust",
                "-f", "/app/locustfile.py",
                "--headless",
                "--users", str(request.users),
                "--spawn-rate", str(request.users // 2 if request.users > 2 else 1),
                "--run-time", f"{request.duration}s",
                "--host", "http://127.0.0.1:8000",
                "--csv", "/app/locust_stats",
                "--html", "/app/locust_report.html",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # This is non-blocking in async
            stdout, stderr = await process.communicate()
            await asyncio.sleep(2)

            # try: Parse CSV and capture panels
            stats = {}
            csv_error = None
            grafana_panels = {}

            try:
                with open("/app/locust_stats_stats.csv", "r") as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)

                    if rows:
                        agg_row = rows[-1]
                        stats = {
                            "total_requests": int(agg_row.get("Request Count", 0)),
                            "failures": int(agg_row.get("Failure Count", 0)),
                            "avg_response_time": float(agg_row.get("Average Response Time", 0)),
                            "requests_per_sec": float(agg_row.get("Requests/s", 0)),
                            "min_response_time": float(agg_row.get("Min Response Time", 0)),
                            "max_response_time": float(agg_row.get("Max Response Time", 0))
                        }
                    
                grafana_base = os.getenv("GF_BROWSER_URL", "https://improved-system-9q56x4x6vpf7p94-3000.app.github.dev")

                # Calculate time range for the test that just ran
                buffer_ms = min(60000, request.duration * 1000 // 2)
                end_time = int(datetime.now().timestamp() * 1000)
                start_time = end_time - (request.duration * 1000) - buffer_ms

                grafana_panels = {
                    "grafana_panel_6": f"{grafana_base}/d-solo/main-fastapi?orgId=1&panelId=6&from={start_time}&to={end_time}&theme=dark",
                    "grafana_panel_8": f"{grafana_base}/d-solo/main-fastapi?orgId=1&panelId=8&from={start_time}&to={end_time}&theme=dark",
                    "grafana_panel_12": f"{grafana_base}/d-solo/main-fastapi?orgId=1&panelId=12&from={start_time}&to={end_time}&theme=dark"
                }
            
            except Exception as e:
                csv_error = str(e)

            return {
                "status": "completed",
                "csv_error": csv_error,
                "locust_stdout": stdout.decode() if stdout else "",
                "locust_stderr": stderr.decode() if stderr else "",
                "return_code": process.returncode,
                **stats,
                **grafana_panels
            }

    except asyncio.TimeoutError:
        return {"status": "timeout", "message": "Load test timed out"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    
@app.get("/get/{short_code}")
async def redirect(short_code: str, request: Request, db: Session = Depends(get_db)):
    try:
        original_url = routes.get(short_code, db)
        if not original_url:
            raise HTTPException(status_code=404, detail=f"Mapping not found - have you shortened this URL yet?")
        
        try:
            # Track the link click or redirect
            click = Click(
                short_code = short_code,
                clicked_at = datetime.utcnow(),
                job_posting_url = request.query_params.get("job_posting_url"),
                resume_version = request.query_params.get("resume_version"),
                user_agent = request.headers.get("user-agent"),
                referrer = request.headers.get("referer")
            )
            db.add(click)
            db.commit()
        except Exception as e:
            db.rollback()
            raise
        
        return RedirectResponse(url=original_url, status_code=302)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/shorten", response_model=ShortenResponse)
async def shorten_request(request: ShortenRequest, db: Session = Depends(get_db)):
    if not request.url.startswith(("http://", "https://")):
        request.url = "http://" + request.url
    short_code = create_short_code()
    short_url = "https://improved-system-9q56x4x6vpf7p94-8000.app.github.dev/get/" + short_code
    routes.save(short_code, request.url, db)
    return {"short_code": short_code, "short_url": short_url}

@app.get("/metrics")
def metrics():
    return Response(
        content = generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )