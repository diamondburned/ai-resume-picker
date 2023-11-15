#!/usr/bin/env python3

import uvicorn
from fastapi import FastAPI


app = FastAPI()


@app.get("/")
async def index():
    return {"Hello": "World"}


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
