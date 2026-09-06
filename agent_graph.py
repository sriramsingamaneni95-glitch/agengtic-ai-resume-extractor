
from dataclasses import dataclass, field
from typing import Callable, Optional, Any


@dataclass
class AgentState:
    resume_text: str
    resume_name: str = "resume.txt"
    jd_text: Optional[str] = None

    plan: dict = field(default_factory=dict)
    data: Optional[Any] = None                     
    raw_extraction_error: Optional[str] = None
    extraction_attempts: int = 0

    low_confidence_fields: list = field(default_factory=list)
    ats_result: Optional[Any] = None
    match_result: Optional[Any] = None
    diff: Optional[dict] = None
    similar_resumes: list = field(default_factory=list)

    log: list = field(default_factory=list)        
    def trace(self, node_name: str):
        self.log.append(node_name)


class AgentGraph:
    def __init__(self):
        self.nodes: dict[str, Callable] = {}
        self.routers: dict[str, Callable] = {}
        self.entry: Optional[str] = None

    def add_node(self, name: str, fn: Callable):
        self.nodes[name] = fn

    def add_router(self, name: str, router_fn: Callable):
        self.routers[name] = router_fn

    def set_entry(self, name: str):
        self.entry = name

    def run(self, state: AgentState, max_steps: int = 25) -> AgentState:
        current = self.entry
        steps = 0
        while current and current != "END" and steps < max_steps:
            state.trace(current)
            state = self.nodes[current](state)
            router = self.routers.get(current)
            current = router(state) if router else "END"
            steps += 1
        return state
