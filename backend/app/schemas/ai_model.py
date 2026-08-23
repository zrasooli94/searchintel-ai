from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AIModelCreate(BaseModel):
    name: str
    provider_model_id: str
    is_active: bool = True


class AIModelRead(BaseModel):
    id: int
    engine_id: int
    name: str
    provider_model_id: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
