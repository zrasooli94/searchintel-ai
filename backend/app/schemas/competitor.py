from pydantic import BaseModel


class CompetitorCandidate(BaseModel):
    name: str
    normalized_name: str
    response_count: int
    mention_count: int
    confidence: float


class ResolveCompetitorsRequest(BaseModel):
    names: list[str]


class ResolvedCompetitor(BaseModel):
    brand_id: int
    name: str
    normalized_name: str
    role: str


class ResolveCompetitorsResult(BaseModel):
    project_id: int
    resolved_count: int
    competitors: list[ResolvedCompetitor]
