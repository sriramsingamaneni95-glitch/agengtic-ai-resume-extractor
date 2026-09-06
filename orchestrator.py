
import re
from concurrent.futures import ThreadPoolExecutor

from agent_graph import AgentGraph, AgentState
from agents.planning_agent import plan_extraction
from agents.extraction_agent import extract_resume_json
from agents.reflection_agent import self_reflect
from agents.validation_agent import validate_resume, needs_human_review
from agents.verification_agent import verify_low_confidence_fields
from agents.scoring_agent import compute_resume_intelligence, compute_ats_score
from agents.recommendation_agent import match_resume_to_jd
from memory import save_version
from semantic_memory import store_memory, retrieve_similar
from utils.logging_config import logger


def node_plan(state: AgentState) -> AgentState:
    state.plan = plan_extraction(state.resume_text)
    logger.info(f"Plan: {state.plan}")
    return state


def node_clean_text(state: AgentState) -> AgentState:
    state.resume_text = re.sub(r"[^\x20-\x7E\n]+", " ", state.resume_text)
    logger.info("Cleaned messy/OCR-like text before extraction.")
    return state


def node_extract(state: AgentState) -> AgentState:
    state.extraction_attempts += 1
    try:
        state.data = extract_resume_json(state.resume_text, state.plan)
        state.raw_extraction_error = None
    except Exception as e:
        state.raw_extraction_error = str(e)
        logger.warning(f"Extraction attempt {state.extraction_attempts} failed: {e}")
    return state


def node_reflect(state: AgentState) -> AgentState:
    state.data = self_reflect(state.data, state.resume_text)
    return state


def node_validate(state: AgentState) -> AgentState:
    state.data = validate_resume(state.data)
    state.low_confidence_fields = needs_human_review(state.data)
    return state


def node_targeted_verification(state: AgentState) -> AgentState:
    state.data = verify_low_confidence_fields(state.data, state.resume_text, state.low_confidence_fields)
    state.low_confidence_fields = needs_human_review(state.data)  
    return state


def node_score(state: AgentState) -> AgentState:
    with ThreadPoolExecutor(max_workers=3) as ex:
        intel_future = ex.submit(compute_resume_intelligence, state.data)
        ats_future = ex.submit(compute_ats_score, state.resume_text, state.jd_text) if state.jd_text else None
        match_future = ex.submit(match_resume_to_jd, state.data, state.jd_text) if state.jd_text else None

        state.data.intelligence = intel_future.result()
        state.ats_result = ats_future.result() if ats_future else None
        state.match_result = match_future.result() if match_future else None
    return state


def node_memory(state: AgentState) -> AgentState:
    state.diff = save_version(state.resume_name, state.data.model_dump())

    try:
        summary_text = state.data.summary or " ".join(state.data.skills) or state.data.name
        state.similar_resumes = retrieve_similar(summary_text, top_k=3)
        store_memory(
            state.resume_name,
            summary_text,
            {"name": state.data.name, "seniority": getattr(state.data.intelligence, "seniority_level", None)},
        )
    except Exception as e:
        logger.warning(f"Semantic memory step skipped (non-critical): {e}")

    return state

def router_plan(state: AgentState) -> str:
    return "clean_text" if state.plan.get("is_scanned_or_messy") else "extract"


def router_clean_text(state: AgentState) -> str:
    return "extract"


def router_extract(state: AgentState) -> str:
    if state.raw_extraction_error and state.extraction_attempts < 3:
        return "extract"        
    if state.raw_extraction_error:
        return "END"              
    return "reflect"


def router_reflect(state: AgentState) -> str:
    return "validate"


def router_validate(state: AgentState) -> str:
    return "targeted_verification" if state.low_confidence_fields else "score"


def router_targeted_verification(state: AgentState) -> str:
    return "score"


def router_score(state: AgentState) -> str:
    return "memory"


def router_memory(state: AgentState) -> str:
    return "END"


def build_graph() -> AgentGraph:
    graph = AgentGraph()
    for name, fn in [
        ("plan", node_plan),
        ("clean_text", node_clean_text),
        ("extract", node_extract),
        ("reflect", node_reflect),
        ("validate", node_validate),
        ("targeted_verification", node_targeted_verification),
        ("score", node_score),
        ("memory", node_memory),
    ]:
        graph.add_node(name, fn)

    for name, router in [
        ("plan", router_plan),
        ("clean_text", router_clean_text),
        ("extract", router_extract),
        ("reflect", router_reflect),
        ("validate", router_validate),
        ("targeted_verification", router_targeted_verification),
        ("score", router_score),
        ("memory", router_memory),
    ]:
        graph.add_router(name, router)

    graph.set_entry("plan")
    return graph


def run_pipeline(resume_text: str, resume_name: str = "sample_resume.txt",
                  jd_text: str | None = None) -> dict:
    logger.info("=== Agent graph run start ===")
    state = AgentState(resume_text=resume_text, resume_name=resume_name, jd_text=jd_text)
    graph = build_graph()
    state = graph.run(state)

    if state.raw_extraction_error:
        raise RuntimeError(
            f"Extraction failed after {state.extraction_attempts} attempts: {state.raw_extraction_error}"
        )

    logger.info(f"Agent path taken: {' -> '.join(state.log)}")

    return {
        "data": state.data.model_dump(),
        "low_confidence_fields": state.low_confidence_fields,
        "ats_result": state.ats_result.model_dump() if state.ats_result else None,
        "match_result": state.match_result.model_dump() if state.match_result else None,
        "changes_since_last_version": state.diff,
        "similar_past_resumes": state.similar_resumes,
        "agent_trace": state.log,
    }
