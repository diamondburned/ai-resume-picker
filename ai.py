import os
import dbm
import json
import numpy
import numpy.linalg
import hashlib
import base64
import openai
import openai.types
from resume import *
from dotenv import load_dotenv

load_dotenv()


# The model to use for text embedding.
EMBEDDINGS_MODEL = "text-embedding-ada-002"

# The path to the cache of embeddings.
EMBEDDINGS_CACHE_PATH = "data/embeddings.dbm"


os.makedirs(os.path.dirname(EMBEDDINGS_CACHE_PATH), exist_ok=True)
embeddings_cache = dbm.open(EMBEDDINGS_CACHE_PATH, "c")


openai_client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def cosine_similarity(a: list[float], b: list[float]) -> float:
    return numpy.dot(a, b) / (numpy.linalg.norm(a) * numpy.linalg.norm(b))


def hash_input(input: str) -> str:
    hash = hashlib.sha256()
    hash.update(input.encode("utf-8"))
    return base64.b64encode(hash.digest()).decode("utf-8")


async def get_embeddings(inputs: list[str], cache=True) -> list[list[float]]:
    # sanitize whitespace
    inputs = [input.replace("\n", " ").strip() for input in inputs]

    uncached: list[str] = []
    embeddings: list[list[float]] = [[]] * len(inputs)
    input_hashes: list[str] | None = None

    if cache:
        input_hashes = [hash_input(input) for input in inputs]
        for i in range(len(inputs)):
            input = inputs[i]
            input_hash = input_hashes[i]
            if input_hash in embeddings_cache:
                embedding = json.loads(embeddings_cache[input_hash])
                embeddings[i] = embedding
            else:
                uncached.append(input)
    else:
        uncached = inputs

    if len(uncached) > 0:
        response = await openai_client.embeddings.create(
            input=uncached,
            model=EMBEDDINGS_MODEL,
        )

        for i in range(len(uncached)):
            embedding = response.data[i].embedding
            embeddings[i] = embedding
            if cache:
                assert input_hashes is not None
                embeddings_cache[input_hashes[i]] = json.dumps(embedding)

    return embeddings


async def search_embeddings(query: str, embeddings: list[list[float]]) -> list[int]:
    """
    Search the list of embeddings for the closest match to the query.
    It returns a list of indices, sorted by closeness to the query.
    """
    query_embedding = (await get_embeddings([query], cache=False))[0]
    return sorted(
        range(len(embeddings)),
        key=lambda i: cosine_similarity(query_embedding, embeddings[i]),
        reverse=True,
    )


async def resume_embeddings(resume: Resume):
    work_embeddings = await get_embeddings(
        [
            f"{work.position} at {work.company}.\n{' '.join(work.highlights)}"
            for work in resume.work
        ]
    )
    print(len(work_embeddings), [len(embedding) for embedding in work_embeddings])

    print("For 'Amazon':")

    result = await search_embeddings("Amazon", work_embeddings)
    print(result)

    result = [resume.work[i] for i in result]
    print([f"{work.position} at {work.company}" for work in result])
