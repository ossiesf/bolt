from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse

from app.shortener import shorten_url, get_original_url
app = FastAPI()

@app.get('/{short_code}')
async def redirect(short_code: str):
    original_url = get_original_url(short_code)

    if not original_url:
        raise HTTPException(status_code=404, detail="URL not found - have you shortened it yet?")
    
    return RedirectResponse(original_url, status_code=302)

@app.get('/original-urls/{code}')
async def get_url(code: str):
    return get_original_url(code)

@app.post('/shorten')
async def shorten_request(original_url: str):
    return shorten_url(original_url)