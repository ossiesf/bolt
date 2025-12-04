from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse

from app.routes import Routes

from app.shortener import create_short_code
from app.models import ShortenRequest, ShortenResponse

routes = Routes()
app = FastAPI()

@app.get('/{short_code}')
async def redirect(short_code: str):
    original_url = routes.get(short_code)

    if not original_url:
        raise HTTPException(status_code=404, detail="URL not found - have you shortened it yet?")
    
    return RedirectResponse(url=original_url, status_code=302)

@app.get('/original-urls/{short_code}')
async def get_url(short_code: str):
    return routes.get(short_code)

@app.post('/shorten', response_model=ShortenResponse)
async def shorten_request(request: ShortenRequest):
    short_code = create_short_code()
    short_url = 'http://localhost:8000/' + short_code
    routes.save(short_code, request.url)
    return {'short_code': short_code, 'short_url': short_url}