import httpx
from pydantic import BaseModel


class Location(BaseModel):
    address: str | None = None


class Basics(BaseModel):
    email: str | None = None
    name: str | None = None
    website: str | None = None
    phone: str | None = None
    location: Location | None = None


class Education(BaseModel):
    institution: str | None = None
    location: str | None = None
    studyType: str | None = None
    area: str | None = None
    startDate: str | None = None
    endDate: str | None = None


class Experience(BaseModel):
    highlights: list[str] | None = None
    company: str | None = None
    position: str | None = None
    location: str | None = None
    startDate: str | None = None
    endDate: str | None = None


class Skill(BaseModel):
    level: str | None = None
    keywords: list[str] | None = None
    name: str | None = None


class Project(BaseModel):
    description: str | None = None
    keywords: list[str] | None = None
    name: str | None = None
    url: str | None = None


class Award(BaseModel):
    summary: str | None = None
    title: str | None = None
    date: str | None = None


class Resume(BaseModel):
    selectedTemplate: int = 0
    basics: Basics = Basics()
    education: list[Education] = []
    work: list[Experience] = []
    skills: list[Skill] = []
    projects: list[Project] = []
    awards: list[Award] = []
    sections: list[str] = []


async def generate_pdf(resume: Resume) -> bytes:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://resumake.io/api/generate/resume",
            json=resume.dict(),
        )
        return response.content
