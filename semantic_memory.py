
import json
from pathlib import Path
from llm_client import get_client

STORE_FILE = Path("semantic_memory.json")


def _embed(text: str) -> list[float]:
    client = get_client()
    resp = client.embeddings.create(model="text-embedding-3-small", input=text[:8000])
    return resp.data[0].embedding


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5
    return dot / (norm_a * norm_b + 1e-8)


def _load() -> list:
    if STORE_FILE.exists():
        return json.loads(STORE_FILE.read_text(encoding="utf-8"))
    return []


def store_memory(resume_name: str, summary_text: str, metadata: dict):
    store = _load()
    embedding = _embed(summary_text)
    store.append({"resume_name": resume_name, "embedding": embedding, "metadata": metadata})
    STORE_FILE.write_text(json.dumps(store), encoding="utf-8")


def retrieve_similar(query_text: str, top_k: int = 3) -> list[dict]:
    store = _load()
    if not store:
        return []
    query_emb = _embed(query_text)
    scored = [(_cosine(query_emb, s["embedding"]), s) for s in store]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [{"score": round(score, 3), **s["metadata"], "resume_name": s["resume_name"]}
            for score, s in scored[:top_k]]
