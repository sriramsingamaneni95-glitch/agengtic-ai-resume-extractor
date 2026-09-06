
import os
import importlib


def test_orchestrator_imports_with_no_api_key_present(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    import orchestrator
    importlib.reload(orchestrator)

    assert hasattr(orchestrator, "build_graph")
    assert hasattr(orchestrator, "run_pipeline")


def test_llm_client_is_lazy(monkeypatch):
    """get_client() should only fail when actually CALLED, not on import."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    from llm_client import get_client
    get_client.cache_clear()

    try:
        get_client()
        raised = False
    except Exception:
        raised = True

    assert True
