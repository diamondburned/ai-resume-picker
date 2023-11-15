#!/usr/bin/env python3
import asyncio
from resume import *
from ai import *


async def main() -> None:
    resume: Resume
    with open("testdata/resume.json", "r") as f:
        resume = Resume.model_validate_json(f.read())

    await resume_embeddings(resume)


if __name__ == "__main__":
    asyncio.run(main())
