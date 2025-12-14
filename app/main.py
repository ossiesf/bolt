from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse

from app.routes import Routes

from app.shortener import create_short_code
from app.models import ShortenRequest, ShortenResponse

routes = Routes()
app = FastAPI()

# Routes are in order, if health is after /{short_code} it will never be reached
@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get('/{short_code}')
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

@app.post('/shorten', response_model=ShortenResponse)
async def shorten_request(request: ShortenRequest):
    if not request.url.startswith(('http://', 'https://')):
        request.url = 'http://' + request.url
    short_code = create_short_code()
    short_url = 'https://improved-system-9q56x4x6vpf7p94-8000.app.github.dev/' + short_code
    routes.save(short_code, request.url)
    return {'short_code': short_code, 'short_url': short_url}