
from functools import lru_cache
from openai import OpenAI


@lru_cache
def get_client() -> OpenAI:
    return OpenAI()
