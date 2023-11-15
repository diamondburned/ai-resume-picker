import httpx
from pydantic import BaseModel


class Location(BaseModel):
    address: str


class Basics(BaseModel):
    email: str
    name: str
    website: str
    phone: str
    location: Location


class Education(BaseModel):
    institution: str
    location: str
    studyType: str
    area: str
    startDate: str
    endDate: str


class Experience(BaseModel):
    highlights: list[str]
    company: str
    position: str
    location: str
    startDate: str
    endDate: str


class Skill(BaseModel):
    level: str | None = None
    keywords: list[str]
    name: str


class Project(BaseModel):
    description: str
    keywords: list[str]
    name: str
    url: str


class Award(BaseModel):
    summary: str
    title: str
    date: str


class Resume(BaseModel):
    selectedTemplate: int
    basics: Basics
    education: list[Education]
    work: list[Experience]
    skills: list[Skill]
    projects: list[Project]
    awards: list[Award]
    sections: list[str]


async def generate_pdf(resume: Resume) -> bytes:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://resumake.io/api/generate/resume",
            json=resume.dict(),
        )
        return response.content
