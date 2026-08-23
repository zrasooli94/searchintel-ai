from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BrandCreate(BaseModel):
    name: str
    description: str | None = None


class BrandRead(BaseModel):
    id: int
    name: str
    normalized_name: str
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)