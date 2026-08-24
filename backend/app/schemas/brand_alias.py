from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BrandAliasCreate(BaseModel):
    alias: str


class BrandAliasRead(BaseModel):
    id: int
    brand_id: int
    alias: str
    normalized_alias: str
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )
