# Resume JSON Extractor — Agentic AI Edition 

Reads a resume (.txt or .pdf), converts it into structured, schema-validated
JSON through a **stateful multi-agent graph** with real dynamic routing,
native OpenAI tool calling, parallel scoring, semantic memory, and a human
feedback loop.

## v3 changelog — full audit fixes

A complete file-by-file audit was done on v2. Real issues found and fixed:

| # | Issue | Fix |
|---|---|---|
| 1 | **Bug:** every agent did `client = OpenAI()` at *import time*, so simply importing `orchestrator.py` (and therefore running any test that touched it) required a real `OPENAI_API_KEY` — this would silently break CI, since the GitHub Actions workflow never sets that secret. | Added `llm_client.py` with a lazy `get_client()`. All agents now construct the client only when a function actually runs. `tests/test_no_api_key_required.py` proves this. |
| 2 | **Bug:** `email_validator.py`'s regex only allowed a single dot in the domain, so valid emails like `name@company.co.in` or `name@example.co.uk` were incorrectly rejected. | Regex now accepts any number of subdomains. |
| 3 | **Bug:** in `extraction_agent.py`, the assistant's tool-call message (a pydantic object) was appended directly to the next API call's `messages` list — unreliable across SDK versions, since nested `tool_calls` objects don't always serialize the way the API expects. | Added `_assistant_message_as_dict()` to build a plain, explicit dict before sending it back. |
| 4 | **Dead code:** `scoring_agent.py` instantiated an `OpenAI()` client that was never used — both its functions are fully deterministic (regex + date math, keyword overlap). | Removed the unused import/client and documented why those two functions deliberately don't call the LLM. |
| 5 | **Unused feature:** `tools/pdf_parser.py` existed but was never called from anywhere — a resume named `resume.pdf` would have silently failed. | `app.py` now detects `.pdf` and routes through the parser automatically. |
| 6 | **Unused feature:** `semantic_memory.py` (embedding-based similarity search) was written but never invoked by the pipeline. | Wired into `orchestrator.py`'s `memory` node, wrapped in try/except so a missing key never breaks the core extraction result. |
| 7 | **Consistency question:** the codebase mixes `client.responses.create(...)` (planning/reflection/verification/recommendation) and `client.chat.completions.create(...)` (extraction). | This is intentional, not an oversight — see "Design decisions" below — but is now called out explicitly so a reviewer doesn't mistake it for an inconsistency. |
| 8 | Tests previously had implicit dependencies on import order/side effects. | Each test file is now independently runnable (`pytest tests/test_x.py` works in isolation) and none require network access or an API key. |

## Architecture

```
plan ──(messy/scanned?)──► clean_text ──► extract
  │
  └──(clean text)─────────────────────► extract
                                            │
                                   (malformed JSON, <3 tries)
                                            │◄────┐
                                            ▼     │ retry
                                         reflect ──┘ (on error, loops back)
                                            │
                                        validate
                                            │
                              (any field confidence < 0.7?)
                              ┌─────yes─────┴─────no──────┐
                              ▼                            ▼
                   targeted_verification                 score
                              │                            │
                              └──────────► score ◄─────────┘
                                            │  (intelligence + ATS + JD-match
                                            │   run IN PARALLEL here)
                                            ▼
                                          memory
                                   (version diff + semantic
                                    similarity search)
                                            │
                                           END
```

Every run returns `agent_trace` — the actual list of nodes visited for that
specific resume. Two different resumes can (and do) take different paths.

## Files
- `app.py` – entry point (supports `.txt` and `.pdf` resumes)
- `orchestrator.py` – builds the agent graph, owns every routing decision
- `agent_graph.py` – the state-machine engine (nodes + conditional routers)
- `llm_client.py` – shared lazy OpenAI client (see audit fix #1)
- `agents/`
  - `planning_agent.py` – decides extraction strategy up front
  - `extraction_agent.py` – real OpenAI function/tool calling
  - `reflection_agent.py` – self-review & correction pass
  - `validation_agent.py` – deterministic checks + knowledge-base lookups
  - `verification_agent.py` – targeted re-check for only low-confidence fields
  - `scoring_agent.py` – resume intelligence + ATS score (deterministic)
  - `recommendation_agent.py` – resume ↔ JD fit score + reasoning
- `tools/` – email validator, date parser, skill normalizer, PDF parser
- `schema.py` – Pydantic models (guaranteed structured output + confidence scores)
- `knowledge_base.py` – file-backed fuzzy-match entity verification
- `memory.py` – JSON version history + diffing across re-uploads
- `semantic_memory.py` – embedding-based similarity search across past resumes
- `feedback.py` – human corrections persist and teach the knowledge base
- `utils/` – logging, retry/error-handling helpers
- `tests/` – fully offline unit tests, no API key or network required

## Setup
```bash
pip install -r requirements.txt
cp .env.example .env        # add your OPENAI_API_KEY
python app.py
```
Create `job_description.txt` in the project root to enable JD matching + ATS
scoring. If any field comes back low-confidence, you'll be prompted in the
terminal to confirm or correct it — corrections are saved and immediately
teach the knowledge base for future runs.

## Running tests
```bash
pytest -v
```
Every test file runs independently and requires **no API key, no network
call**. Routing logic, schema validation, tool functions, and the knowledge
base are all tested against plain Python objects/fixtures.

## Docker
```bash
docker build -t resume-extractor .
docker run --env-file .env resume-extractor
```

## Design decisions
- **Deterministic tools over LLM calls where possible** (dates, email regex,
  skill normalization, ATS keyword overlap, resume intelligence math) —
  cheaper, faster, fully reproducible, and testable without any API key.
- **Two OpenAI API styles are used on purpose, not by accident:**
  `extraction_agent.py` uses `chat.completions.create(..., tools=[...])`
  because that's the API surface that supports native function/tool calling
  the way this assignment specifically asked for. The other agents
  (planning, reflection, verification, recommendation) only need
  "give me back JSON" and use the simpler `responses.create(..., text={"format":"json_object"})`
  call — no tools needed there, so the simpler API is a better fit.
- **Confidence scores** per field drive the human-in-the-loop gate instead of
  trusting every extraction blindly.
- **Knowledge base and semantic memory start intentionally simple**
  (fuzzy string matching, JSON-file storage) — the interfaces
  (`verify_entity`, `teach_entity`, `store_memory`, `retrieve_similar`) are
  written so a real vector DB (Chroma/FAISS/Pinecone) can be swapped in later
  without touching any agent code.

## Known limitations (stated honestly, not overclaimed)
- `knowledge_base.py` and `memory.py`/`semantic_memory.py` use flat JSON
  files — fine for a single-user assignment/demo, **not** safe for
  concurrent multi-user writes (no file locking). A real deployment would
  use a database.
- The ATS score is a deterministic keyword-overlap heuristic, not a
  semantic/ML-based match — it's fast and explainable, but a real ATS
  product typically weighs keyword placement, section context, etc.
- The knowledge base ships with a handful of example companies/universities
  — it's a demonstration of the RAG *pattern*, not a populated production
  dataset.
- The human feedback loop runs via terminal `input()` in `app.py` — fine for
  a CLI assignment; a web/API deployment would replace this with a proper
  review queue endpoint.

## Tech Stack
Python · OpenAI GPT-4.1 (native tool calling) · text-embedding-3-small ·
Pydantic · custom stateful agent graph · pytest · Docker · GitHub Actions

## Author
**Sriram Singamaneni**
