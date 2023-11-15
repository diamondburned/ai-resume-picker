from fastapi import FastAPI


api = FastAPI()


@api.get("/")
async def index():
    return {"Hello": "World"}
