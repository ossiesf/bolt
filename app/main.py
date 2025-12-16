import asyncio
import csv

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.database import Base, Session, engine
from app.models import ShortenRequest, ShortenResponse
from app.routes import Routes, get_db
from app.shortener import create_short_code


routes = Routes()
app = FastAPI()

app.mount("/static", StaticFiles(directory="web"), name="static")

@app.on_event("startup")
def startup():
    # Create tables
    Base.metadata.create_all(bind=engine)
    
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

@app.post("/api/run-load-test")
async def run_load_test(request: LoadTestRequest):
    try:
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

        # Parse CSV...
        stats = {}
        csv_error = None
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
        except Exception as e:
            csv_error = str(e)

        return {
            "status": "completed",
            "csv_error": csv_error,
            "locust_stdout": stdout.decode() if stdout else "",
            "locust_stderr": stderr.decode() if stderr else "",
            "return_code": process.returncode,
            **stats
        }

    except asyncio.TimeoutError:
        return {"status": "timeout", "message": "Load test timed out"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    
@app.get("/get/{short_code}")
async def redirect(short_code: str, db: Session = Depends(get_db)):
    try:
        original_url = routes.get(short_code, db)
        if not original_url:
            raise HTTPException(status_code=404, detail=f"Mapping not found - have you shortened this URL yet?")
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