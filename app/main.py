from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse

from app.shortener import shorten_url, get_original_url
from app.models import ShortenRequest, ShortenResponse

app = FastAPI()

@app.get('/{short_code}')
async def redirect(short_code: str):
    original_url = get_original_url(short_code)

    if not original_url:
        raise HTTPException(status_code=404, detail="URL not found - have you shortened it yet?")
    
    return RedirectResponse(url=original_url, status_code=302)

@app.get('/original-urls/{code}')
async def get_url(code: str):
    return get_original_url(code)

@app.post('/shorten', response_model=ShortenResponse)
async def shorten_request(request: ShortenRequest):
    short_code = shorten_url(request.url)
    short_url = 'http://localhost:8000/' + short_code
    return {'short_code': short_code, 'short_url': short_url}