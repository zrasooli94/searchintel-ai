from datetime import datetime

from pydantic import BaseModel, ConfigDict, HttpUrl


class WebsiteCreate(BaseModel):
    base_url: HttpUrl
    is_primary: bool = True


class WebsiteRead(BaseModel):
    id: int
    brand_id: int
    domain: str
    base_url: str
    is_primary: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)