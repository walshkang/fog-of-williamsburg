from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class BoroughBase(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


class BoroughDetail(BoroughBase):
    total_area: float
    # Geometry is returned as GeoJSON-like dict
    geometry: dict | None = None


class UserCreate(BaseModel):
    id: str = Field(..., description="Client-generated user identifier (UUID string).")
    chosen_borough_id: int | None = None


class UserRead(BaseModel):
    id: str
    chosen_borough_id: int | None
    created_at: datetime

    class Config:
        orm_mode = True


class GPXUploadResponse(BaseModel):
    activity_id: int
    status: Literal["processing", "completed"] = "completed"


class CheckinRequest(BaseModel):
    latitude: float
    longitude: float


class CoreScore(BaseModel):
    borough_id: int
    borough_name: str
    percent_explored: float
    total_area: float
    unveiled_area: float


class Mission(BaseModel):
    id: str
    title: str
    description: str
    achieved: bool


