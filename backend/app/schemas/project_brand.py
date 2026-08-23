from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class ProjectBrandCreate(BaseModel):
    brand_id: int
    role: Literal["target", "competitor"]


class ProjectBrandRead(BaseModel):
    id: int
    project_id: int
    brand_id: int
    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)