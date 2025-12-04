from pydantic import BaseModel

class ShortenRequest(BaseModel):
    url: str

class ShortenResponse(BaseModel):
    short_url: str
    short_code: str