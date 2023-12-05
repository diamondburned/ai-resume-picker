import os
import json
import numpy
import numpy.linalg
import hashlib
import base64
import openai
import openai.types
import asyncio
import dbm.dumb as db
from typing import Any, Callable, MutableMapping, Generator, TypeVar
from resume import *
from dotenv import load_dotenv

load_dotenv()


# The model to use for text embedding.
EMBEDDINGS_MODEL = "text-embedding-ada-002"

# The path to the cache of embeddings.
EMBEDDINGS_CACHE_PATH = "data/embeddings.dbm"


def get_embeddings_cache() -> MutableMapping:
    os.makedirs(os.path.dirname(EMBEDDINGS_CACHE_PATH), exist_ok=True)
    return db.open(EMBEDDINGS_CACHE_PATH, "c")


openai_client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def cosine_similarity(a: list[float], b: list[float]) -> float:
    return numpy.dot(a, b) / (numpy.linalg.norm(a) * numpy.linalg.norm(b))


def hash_input(input: str) -> str:
    hash = hashlib.sha256()
    hash.update(input.encode("utf-8"))
    return base64.b64encode(hash.digest()).decode("utf-8")


Embeddings = list[list[float]]


async def get_embeddings(inputs: list[str], cache=True) -> Embeddings:
    # sanitize whitespace
    inputs = [input.replace("\n", " ").strip() for input in inputs]

    uncached: list[int] = []
    embeddings: list[list[float]] = [[]] * len(inputs)
    input_hashes: list[str] | None = None

    if cache:
        embeddings_cache = get_embeddings_cache()
        input_hashes = [hash_input(input) for input in inputs]
        for i in range(len(inputs)):
            input = inputs[i]
            input_hash = input_hashes[i]
            if input_hash in embeddings_cache:
                embedding = json.loads(embeddings_cache[input_hash])
                embeddings[i] = embedding
            else:
                uncached.append(i)
    else:
        uncached = list(range(len(inputs)))

    if len(uncached) > 0:
        response = await openai_client.embeddings.create(
            input=[inputs[i] for i in uncached],
            model=EMBEDDINGS_MODEL,
        )

        for i in range(len(uncached)):
            embeddings[uncached[i]] = response.data[i].embedding

        if cache:
            assert input_hashes is not None
            embeddings_cache = get_embeddings_cache()
            for i in range(len(embeddings)):
                input_hash = input_hashes[i]
                embeddings_cache[input_hash] = json.dumps(embeddings[i])

    return embeddings


ListItemT = TypeVar("ListItemT")


async def get_list_embeddings(
    inputs: list[ListItemT],
    mapper: Callable[[ListItemT], str],
) -> Embeddings:
    return await get_embeddings([mapper(input) for input in inputs])


async def search_embeddings(query: str, embeddings: Embeddings) -> list[int]:
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


async def search_list(
    inputs: list[ListItemT],
    mapper: Callable[[ListItemT], str],
    query: str,
) -> list[ListItemT]:
    """
    Search the list of inputs for the closest match to the query.
    It returns a list of inputs, sorted by closeness to the query.
    """
    embeddings = await get_list_embeddings(inputs, mapper)
    result = await search_embeddings(query, embeddings)
    return [inputs[i] for i in result]


async def resume_embeddings(resume: Resume):
    assert len(resume.work) < 20
    assert len(resume.projects) < 20
    assert len(resume.education) < 10
    assert len(resume.awards) < 10

    work_embeddings = await get_list_embeddings(
        resume.work,
        lambda w: f"{w.position} at {w.company}.\n{' '.join(w.highlights or [])}",
    )
    print(len(work_embeddings), [len(embedding) for embedding in work_embeddings])

    company = "Amazon"

    q = f"Top work experiences for applying to '{company}':"
    print(q)

    result = await search_embeddings(q, work_embeddings)
    print(result)

    result = [resume.work[i] for i in result]
    print([f"{work.position} at {work.company}" for work in result])


class ResumeSorter:
    """
    Sorts a resume by relevance to a search query.
    It automatically uses the OpenAI Embeddings API to generate embeddings and
    cache them for future use.
    """

    search: str
    _resume: Resume

    def __init__(self, resume: Resume, search: str = ""):
        assert len(resume.work) < 20
        assert len(resume.projects) < 20
        assert len(resume.education) < 10
        assert len(resume.awards) < 10

        self.search = search
        self.resume = resume

    @property
    def resume(self) -> Resume:
        return self._resume

    @resume.setter
    def resume(self, resume: Resume):
        self._resume = resume.model_copy(deep=True)

    async def sort(
        self,
        work=True,
        projects=True,
        education=True,
        awards=True,
    ):
        coros = []
        if work:
            coros.append(self._sort_work())
        if projects:
            coros.append(self._sort_projects())
        if education:
            coros.append(self._sort_education())
        if awards:
            coros.append(self._sort_awards())

        await asyncio.gather(*coros)

    async def _sort_work(self):
        self._resume.work = await search_list(
            self._resume.work,
            lambda w: f"{w.position} at {w.company}.\n{' '.join(w.highlights or [])}",
            self.search,
        )

    async def _sort_projects(self):
        self._resume.projects = await search_list(
            self._resume.projects,
            lambda p: f"{p.name}: \n{p.description} ({' '.join(p.keywords or [])})",
            self.search,
        )

    async def _sort_education(self):
        self._resume.education = await search_list(
            self._resume.education,
            lambda e: f"{e.institution} ({e.studyType}, {e.area}): {e.startDate} - {e.endDate}",
            self.search,
        )

    async def _sort_awards(self):
        self._resume.awards = await search_list(
            self._resume.awards,
            lambda a: f"{a.title}: {a.summary} ({a.date})",
            self.search,
        )
