"""
Single lazy-loaded OpenAI client shared by all agents.

WHY THIS FILE EXISTS (bug fix): every agent previously did
`client = OpenAI()` at MODULE IMPORT TIME. That means simply importing
orchestrator.py (which imports every agent) required a valid
OPENAI_API_KEY to even exist as an environment variable - so pytest
would crash on collection in CI/any machine without the key set, even
for tests that never call the API (e.g. routing-logic tests).

get_client() defers construction until an agent function actually runs,
so importing the code and testing pure logic needs no API key at all.
"""
from functools import lru_cache
from openai import OpenAI


@lru_cache
def get_client() -> OpenAI:
    return OpenAI()
