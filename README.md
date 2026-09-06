# 🤖 Agentic AI Resume Extractor

![Python](https://img.shields.io/badge/Python-3.11-blue)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4.1-412991)
![Tests](https://img.shields.io/badge/tests-pytest-green)
![Docker](https://img.shields.io/badge/containerized-Docker-2496ED)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

A multi-agent AI system that reads a resume (`.txt` or `.pdf`) and turns it
into structured, schema-validated JSON — through a **stateful agent graph**
with real dynamic routing, native OpenAI tool calling, parallel scoring,
semantic memory, and a human-in-the-loop feedback step.

This isn't a single-prompt wrapper around an LLM. It's a planning →
extraction → self-reflection → validation → scoring → recommendation
pipeline, where each stage is an independent agent and the path taken
actually changes based on the resume being processed.

---

## Table of Contents
- [Why this is "agentic"](#why-this-is-agentic)
- [Architecture](#architecture)
- [Features](#features)
- [Project structure](#project-structure)
- [Setup](#setup)
- [Usage](#usage)
- [Running tests](#running-tests)
- [Docker](#docker)
- [Design decisions](#design-decisions)
- [Known limitations](#known-limitations)
- [Tech stack](#tech-stack)

---

## Why this is "agentic"

| Capability | Where |
|---|---|
| Planning before acting | `agents/planning_agent.py` decides an extraction strategy before any extraction happens |
| Native tool calling | `agents/extraction_agent.py` — the model itself decides when to call `validate_email`, `parse_date`, `normalize_skill` via OpenAI's function-calling API |
| Self-reflection | `agents/reflection_agent.py` reviews and corrects its own extraction |
| Multi-agent collaboration | Extraction → Validation → Scoring → Recommendation, each a separate agent with a defined input/output |
| Real dynamic routing | `orchestrator.py` — routing decisions are made at runtime from shared state (messy text → cleanup step; low confidence → targeted verification; malformed JSON → bounded retry loop) |
| Parallel execution | Resume intelligence, ATS scoring, and JD matching run concurrently via `ThreadPoolExecutor` |
| Memory | `memory.py` (version diffing) + `semantic_memory.py` (embedding-based similarity search across past resumes) |
| Human-in-the-loop | Low-confidence fields are flagged for human confirmation; corrections permanently teach the knowledge base |

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

Every run returns `agent_trace` — the literal list of nodes visited. Two
different resumes can (and do) take different paths through the graph.

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
- ✅ Fully offline, independent unit tests (no API key required to run `pytest`)
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

## Setup

```bash
git clone https://github.com/sriramsingamaneni95-glitch/agengtic-ai-resume-extractor.git
cd agengtic-ai-resume-extractor
pip install -r requirements.txt
cp .env.example .env        # add your OPENAI_API_KEY
```

## Usage

Place a resume at `sample_resume.txt` (or `sample_resume.pdf`) in the
project root, then:

```bash
python app.py
```

To also get JD matching + ATS scoring, add a `job_description.txt` file
before running. Output is printed to the console and saved to `output.json`.
If any field comes back low-confidence, you'll be prompted to confirm or
correct it — corrections are saved and immediately teach the knowledge base.

## Running tests

```bash
pytest -v
```

Every test file runs independently and requires **no API key and no
network access** — routing logic, schema validation, tools, and the
knowledge base are all tested against plain Python fixtures.

## Docker

```bash
docker build -t resume-extractor .
docker run --env-file .env resume-extractor
```

## Design decisions

- **Deterministic tools over LLM calls where possible** — dates, email
  validation, skill normalization, ATS keyword overlap, and resume
  intelligence math are all plain Python, not LLM calls. Cheaper, faster,
  reproducible, and testable without hitting the API.
- **Two OpenAI API styles, used intentionally:** `extraction_agent.py` uses
  `chat.completions.create(..., tools=[...])` because that's the surface
  that supports native function/tool calling. The other agents only need
  "return JSON" and use the simpler `responses.create(..., text={"format":"json_object"})`.
- **Confidence scores drive the human-in-the-loop gate** instead of trusting
  every extraction blindly.
- **Knowledge base and semantic memory start simple** (fuzzy matching,
  JSON-file storage) — interfaces are written so a real vector DB
  (Chroma/FAISS/Pinecone) can be swapped in later without touching agent code.

## Known limitations

- Knowledge base / memory files are flat JSON — fine for a single-user demo,
  not safe for concurrent multi-user writes (no file locking).
- ATS scoring is a deterministic keyword-overlap heuristic, not a
  semantic/ML-based match.
- The knowledge base ships with a handful of example companies/universities
  — it demonstrates the RAG *pattern*, not a populated production dataset.
- The human feedback loop runs via terminal `input()` — a web/API deployment
  would replace this with a proper review-queue endpoint.

## Tech stack

Python · OpenAI GPT-4.1 (native tool calling) · text-embedding-3-small ·
Pydantic · custom stateful agent graph · pytest · Docker · GitHub Actions

---

**Author:** Sriram Singamaneni
