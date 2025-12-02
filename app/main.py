from fastapi import FastAPI

app = FastAPI()

@app.get('/urls/{code}')
async def get_url(code: str):
    return code

@app.get('/api/stats')
async def stats():
    return 'stats'

@app.post('/urls')
async def create_url(url: str):
    return 'create_url'