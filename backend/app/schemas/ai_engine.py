from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AIEngineCreate(BaseModel):
    name: str
    slug: str


class AIEngineRead(BaseModel):
    id: int
    name: str
    slug: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
