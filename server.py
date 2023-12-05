#!/usr/bin/env python3

import uvicorn
from pydantic import BaseModel
from fastapi import FastAPI, APIRouter, Query, Response, Body
from fastapi.staticfiles import StaticFiles
from resume import *
from ai import ResumeSorter

api = APIRouter(prefix="/api")


class SortResumeResponse(BaseModel):
    resume: Resume


@api.post("/resume/sort")
async def sort_resume(
    query: str,
    work=True,
    projects=True,
    education=True,
    awards=True,
    resume: Resume = Body(),
) -> SortResumeResponse:
    """
    Sorts a resume by relevance to a search query.
    It automatically uses the OpenAI Embeddings API to generate embeddings and
    cache them for future use.
    """

    sorter = ResumeSorter(resume, query)
    await sorter.sort(work, projects, education, awards)
    return SortResumeResponse(resume=sorter.resume)


@api.post("/resume.pdf")
async def resume_pdf(resume: Resume = Body()) -> Response:
    """
    Generates a PDF of the resume.
    """
    print(resume.dict())
    pdf_data = await generate_pdf(resume)
    return Response(content=pdf_data, media_type="application/pdf")


app = FastAPI()
app.include_router(api)
app.mount("/", StaticFiles(directory="frontend", html=True))


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=9000, reload=True)
