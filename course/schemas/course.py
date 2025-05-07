from pydantic import BaseModel, ConfigDict
from typing import Optional

class CourseBase(BaseModel):
    title: str
    description: Optional[str] = None

class CourseCreate(CourseBase):
    instructor_id: int

class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    instructor_id: Optional[int] = None

class CourseResponse(CourseBase):
    id: int
    instructor_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)