#  Agentic AI Resume Extractor

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4.1-412991?logo=openai&logoColor=white)
![Tests](https://img.shields.io/badge/tests-pytest-0A9EDC?logo=pytest&logoColor=white)
![Docker](https://img.shields.io/badge/containerized-Docker-2496ED?logo=docker&logoColor=white)
![CI](https://img.shields.io/badge/CI-GitHub%20Actions-2088FF?logo=githubactions&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

> Turns a raw resume into structured, validated, scored JSON — through a
> **stateful multi-agent graph**, not a single prompt.

A resume goes in. A planning agent decides how to handle it. An extraction
agent pulls structured fields using **native OpenAI tool calling**. A
reflection agent double-checks its own work. A validation agent
cross-references companies and universities against a knowledge base. If
anything comes back uncertain, a targeted verification agent — or a human —
steps in. Scoring, ATS matching, and JD comparison all run in parallel.
Every decision is traced, every version is remembered.

---

## Table of Contents
- [Evolution of this project](#evolution-of-this-project)
- [Why this is "agentic," not just an API wrapper](#why-this-is-agentic-not-just-an-api-wrapper)
- [Architecture](#architecture)
- [Example output](#example-output)
- [Features](#features)
- [Project structure](#project-structure)
- [Quickstart](#quickstart)
- [Usage](#usage)
- [Running tests](#running-tests)
- [Docker](#docker)
- [Design decisions](#design-decisions)
- [Known limitations](#known-limitations)
- [Tech stack](#tech-stack)

---

## Why this is "agentic," not just an API wrapper

| Capability | Where it lives |
|---|---|
| Plans before acting | `agents/planning_agent.py` assesses the resume (messy? scanned? multi-page?) before extraction starts |
| Calls its own tools | `agents/extraction_agent.py` — the **model itself** decides when to call `validate_email`, `parse_date`, `normalize_skill`, via OpenAI's function-calling API — not post-processing in Python |
| Reflects and self-corrects | `agents/reflection_agent.py` re-reads the source resume and fixes its own extraction |
| Collaborates across specialized agents | Planning → Extraction → Reflection → Validation → (Verification) → Scoring → Recommendation, each with a defined input/output contract |
| Routes dynamically, not linearly | `orchestrator.py` — a messy resume takes a different path than a clean one; a low-confidence field triggers a different path than a confident one; malformed JSON triggers a bounded retry loop |
| Executes in parallel where safe | Resume intelligence, ATS scoring, and JD matching run concurrently via `ThreadPoolExecutor` |
| Remembers across runs | `memory.py` diffs resume versions; `semantic_memory.py` retrieves similar past resumes by *meaning* via embeddings |
| Learns from human correction | `feedback.py` — a human's correction is persisted and immediately teaches the knowledge base, so the same mistake isn't repeated |

## Architecture

```
plan ──(messy/scanned?)──► clean_text ──► extract
  │
  └──(clean text)─────────────────────► extract
                                            │
                                   (malformed JSON, <3 tries)
                                            │◄────┐
                                            ▼     │ retry
                                         reflect ──┘
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
                                            │   run IN PARALLEL)
                                            ▼
                                          memory
                                   (version diff + semantic
                                    similarity search)
                                            │
                                           END
```

Every run returns `agent_trace` — the literal list of nodes visited for
*that specific resume*. Run two different resumes and you'll see two
different traces.

## Example output

```json
{
  "data": {
    "name": "Sriram Singamaneni",
    "email": "sriram@example.com",
    "skills": ["Python", "JavaScript", "Machine Learning"],
    "experience": [
      {
        "company": "Jpmc",
        "title": "Software Engineer",
        "start_date": "2025-06",
        "end_date": "present"
      }
    ],
    "confidence_scores": {"name": 0.98, "email": 0.95, "skills": 0.9},
    "intelligence": {
      "total_experience_years": 3.2,
      "seniority_level": "Mid-level",
      "career_progression_summary": "Software Engineer -> Senior Software Engineer"
    },
    "verified_entities": {"Google": {"verified": true, "matched_to": "Google"}}
  },
  "low_confidence_fields": [],
  "ats_result": {"ats_score": 78.5, "missing_keywords": ["kubernetes", "graphql"]},
  "agent_trace": ["plan", "extract", "reflect", "validate", "score", "memory"]
}
```

## Features

- ✅ Structured extraction with guaranteed JSON Schema (Pydantic)
- ✅ Per-field confidence scores
- ✅ Human-in-the-loop review for low-confidence fields
- ✅ Knowledge-base verification of companies/universities (fuzzy matching)
- ✅ Resume ↔ Job Description fit scoring with reasoning
- ✅ ATS score + missing-keyword recommendations
- ✅ Resume intelligence: years of experience, seniority, leadership signals, career progression
- ✅ Version memory — diffs resumes against previous uploads
- ✅ Semantic memory — finds similar past resumes by meaning, not filename
- ✅ Retry + malformed-JSON recovery
- ✅ Structured logging with latency and token-usage metrics
- ✅ PDF and plain-text resume support
- ✅ Fully offline, independent unit tests — no API key needed to run `pytest`
- ✅ Dockerized, with a GitHub Actions CI workflow

## Project structure

```
.
├── app.py                      # entry point
├── orchestrator.py              # builds the agent graph, owns all routing logic
├── agent_graph.py                # state-machine engine (nodes + routers)
├── llm_client.py                  # shared, lazily-initialized OpenAI client
├── schema.py                       # Pydantic models (structured output + confidence)
├── knowledge_base.py                # fuzzy-match entity verification (file-backed)
├── memory.py                         # version history + diffing
├── semantic_memory.py                 # embedding-based similarity search
├── feedback.py                         # human correction loop
├── agents/
│   ├── planning_agent.py
│   ├── extraction_agent.py              # real OpenAI tool calling
│   ├── reflection_agent.py
│   ├── validation_agent.py
│   ├── verification_agent.py             # targeted re-check for low-confidence fields
│   ├── scoring_agent.py                   # deterministic: intelligence + ATS
│   └── recommendation_agent.py             # resume ↔ JD matching
├── tools/
│   ├── email_validator.py
│   ├── date_parser.py
│   ├── skill_normalizer.py
│   └── pdf_parser.py
├── utils/
│   ├── logging_config.py
│   └── retry.py
├── tests/                                   # fully offline, independent tests
├── .github/workflows/test.yml                # CI: runs pytest on every push
└── Dockerfile
```

## Quickstart

```bash
git clone https://github.com/sriramsingamaneni95-glitch/agentic-ai-resume-extractor.git
cd agentic-ai-resume-extractor
pip install -r requirements.txt
cp .env.example .env        # add your OPENAI_API_KEY
python app.py
```

## Usage

Place a resume at `sample_resume.txt` (or `sample_resume.pdf`) in the
project root, then run `python app.py`. To also get JD matching + ATS
scoring, add a `job_description.txt` file before running.

Output is printed to the console and saved to `output.json`, along with
the `agent_trace` showing exactly which path the graph took. If any field
comes back low-confidence, you'll be prompted in the terminal to confirm
or correct it — corrections are saved and immediately teach the knowledge
base for future runs.

## Running tests

```bash
pytest -v
```

Every test file runs independently and requires **no API key and no
network access** — routing logic, schema validation, tools, and the
knowledge base are all tested against plain Python fixtures, not live
API calls.

## Docker

```bash
docker build -t resume-extractor .
docker run --env-file .env resume-extractor
```

## Design decisions

- **Deterministic tools over LLM calls where possible.** Dates, email
  validation, skill normalization, ATS keyword overlap, and resume
  intelligence math are all plain Python, not LLM calls — cheaper, faster,
  reproducible, and fully testable without hitting the API.
- **Two OpenAI API styles, used intentionally, not inconsistently.**
  `extraction_agent.py` uses `chat.completions.create(..., tools=[...])`
  because that's the surface that supports native function/tool calling.
  Every other agent only needs "return JSON" and uses the simpler
  `responses.create(..., text={"format":"json_object"})`.
- **Confidence scores drive the human-in-the-loop gate** instead of
  trusting every extraction blindly.
- **Knowledge base and semantic memory start simple** (fuzzy string
  matching, JSON-file storage) — the interfaces (`verify_entity`,
  `teach_entity`, `store_memory`, `retrieve_similar`) are written so a real
  vector DB (Chroma/FAISS/Pinecone) can be swapped in later without
  touching any agent code.

## Known limitations

Stated honestly rather than overclaimed:

- Knowledge base / memory files are flat JSON — fine for a single-user
  demo, not safe for concurrent multi-user writes (no file locking).
- ATS scoring is a deterministic keyword-overlap heuristic, not a
  semantic/ML-based match — fast and explainable, but simpler than a
  production ATS.
- The knowledge base ships with a handful of example companies/
  universities — it demonstrates the RAG *pattern*, not a populated
  production dataset.
- The human feedback loop runs via terminal `input()` — a web/API
  deployment would replace this with a proper review-queue endpoint.

## Tech stack

Python · OpenAI GPT-4.1 (native tool calling) · text-embedding-3-small ·
Pydantic · custom stateful agent graph · pytest · Docker · GitHub Actions

---

**Author:** Sriram Singamaneni
