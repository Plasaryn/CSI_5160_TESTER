from pydantic import BaseModel

class Job(BaseModel):
  image_url: str
  iterations: int | None = None

class Host(BaseModel):
  address: str
  hostname: str
  description: str | None = None
