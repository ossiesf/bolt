from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from app.routes import Routes
from app.shortener import create_short_code
from app.models import ShortenRequest, ShortenResponse

import subprocess
import csv

from pydantic import BaseModel


routes = Routes()
app = FastAPI()

app.mount("/static", StaticFiles(directory="web"), name="static")

# Serve the web UI at root
@app.get("/")
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

# Run an actual load test
@app.post("/api/run-load-test") # This is the actual endpoint to run the tests via web
async def run_load_test(request: LoadTestRequest):
    try:
        result = subprocess.run(
    [
        "locust",
        "-f", "/app/locustfile.py",  # Absolute path
        "--headless",
        "--users", str(request.users),
        "--spawn-rate", str(request.users // 2 if request.users > 2 else 1),
        "--run-time", f"{request.duration}s",
        "--host", "http://localhost:8000",
        "--csv", "/app/locust_stats",
        "--html", "/app/locust_report.html"
    ],
    capture_output=True,
    text=True,
    timeout=request.duration + 30
    # Remove cwd="/app" - not needed with absolute paths
)

        # Parse the CSV file
        stats = {}
        csv_error = None
        try:
            with open("/app/locust_stats_stats.csv", "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

                # Get the "Aggregated" row (last row)
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

        except Exception as e:
            csv_error = str(e)

        return {
            "status": "completed",
            "csv_error": csv_error,
            "locust_stdout": result.stdout,  # Full output
            "locust_stderr": result.stderr,   # And stderr
            "return_code": result.returncode,
            **stats
        }
    
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "message": "Load test timed out"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    
@app.get("/get/{short_code}")
async def redirect(short_code: str):
    try:
        original_url = routes.get(short_code)
        if not original_url:
            raise HTTPException(status_code=404, detail=f"Mapping not found - have you shortened this URL yet?")
        return RedirectResponse(url=original_url, status_code=302)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/shorten", response_model=ShortenResponse)
async def shorten_request(request: ShortenRequest):
    if not request.url.startswith(("http://", "https://")):
        request.url = "http://" + request.url
    short_code = create_short_code()
    short_url = "https://improved-system-9q56x4x6vpf7p94-8000.app.github.dev/get/" + short_code
    routes.save(short_code, request.url)
    return {"short_code": short_code, "short_url": short_url}