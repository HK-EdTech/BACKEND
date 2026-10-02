# Agentic homework marking — slice 1: RawHomeworkProcessingAgent

## Context

The OCR-first approach is abandoned. Google Vision reads text but destroys what marking
needs: it mangled `∠POQ` into `ZPOQ` and `△PQR` into `APQR`, lost exponents
(`60² + 144² = 156` → `602 +1442156`), silently corrected students' spelling, and scrambled
reading order on photographed pages. A vision LLM reads the page directly instead.

So `OpenRouterLLM`'s text-only OCR post-processing is replaced by a multi-agent marking
pipeline. This slice builds the **first** agent: given whatever material a teacher uploads,
work out *which questions are to be marked* and produce a canonical question list for the
marking agents that come later. FE/BE integration is out of scope — this is a test harness
behind one endpoint.

## Decisions taken

| | choice |
|---|---|
| framework | LangGraph + LangChain (`langgraph`, `langchain-openai`) |
| transport | FastAPI endpoint, multipart upload |
| models | `qwen/qwen3-vl-32b-instruct` for extraction; `qwen/qwen3-vl-30b-a3b-thinking` for reconciliation, as a one-line-swappable constant to be compared live |
| output | `{"questions": [{"number": "5", "text": "..."}]}`, filtered to required only |
| submissions as a question source | **yes, when the submission is a worksheet** — see below |
| old `/ai/process-ocr`, `/ai/validate-answer` | deleted; `/ai/health` kept |

**Submissions are a valid question source, conditionally.** Many submissions are worksheets:
the question is *printed* on the page and the student writes answers on it. That printed text
is as readable as a question image. What is *not* recoverable is a question from a blank sheet
carrying only the student's working — there, a `text` field would be invention.

So `extract_from_submissions` classifies before it extracts:

| what the image shows | result |
|---|---|
| printed question text present (**worksheet**) | extract number + text normally, confidence capped at 0.85 (handwriting may obscure part of the stem) |
| only handwritten working / answers | contribute **nothing**; if no other source yielded questions → `NO_QUESTIONS_FOUND` |

The prompt must state explicitly that question text is to be transcribed only where it is
actually printed on the page, and never inferred from the student's answer. With a mixed
batch, take the union of questions found across the worksheet-type submissions; if none of
them is a worksheet, the error path stands.

## Part A — rebuild `src/ai_agents/OpenRouterLLM.py`

**Delete:** `process_ocr_result`, `validate_homework_answer`, `_extract_json`,
`_parse_json_response`.

**Keep:** client construction (base_url, key, `HTTP-Referer`/`X-Title`), `load_free_models`,
`health_check`, and the **token accounting** — `total_usage` initialised before the retry
loop, folded per attempt via defensive `getattr(response, "usage", None)`, surfaced as `_meta`.

**Salvage before deleting:** move `_extract_json` / `_parse_json_response` (lines 248-294,
including the truncated-JSON repair) into `src/common/json_extract.py`. They become the last
rung of the structured-output fallback ladder.

**Fix while rebuilding:** success nests usage under `_meta["usage"]` but error paths return
`"usage"` top-level. Make both nest under `_meta`, so callers stop needing
`result.get("_meta", result)`.

**`src/main.py`:** delete `ProcessOcrRequest`, `ValidateAnswerRequest` and their two
endpoints (lines 200-240). Keep `/ai/health`.

## Part B — the agent

### Graph

```
START → plan_sources                         (pure Python, no LLM)
   ├─ question_text present   → classify_question_text      (cheap, TEXT-ONLY)
   ├─ question_images present → extract_from_question_images (cheap VL)
   ├─ else                    → extract_from_marking_scheme  (cheap VL)
   └─ nothing at all          → finalize (error)

classify_question_text →  role=filter      → question images, else marking scheme
                          role=questions   → decide_escalation
                          role=mixed       → extract both, then decide_escalation
                          role=unclear     → decide_escalation (forces escalation)

extract_from_question_images → candidates? decide_escalation : extract_from_marking_scheme
extract_from_marking_scheme  → candidates? decide_escalation : extract_from_submissions
extract_from_submissions     → candidates? decide_escalation : finalize (NO_QUESTIONS_FOUND)
     (worksheet-only: transcribes printed questions, never infers them from answers)

decide_escalation → needs_escalation ? reconcile (thinking, TEXT-ONLY) : apply_filter
reconcile → apply_filter → finalize → END
```

`decide_escalation` is pure Python; it sets `needs_escalation` when candidates come from
more than one source, any confidence < 0.6, `required_numbers` contains a number absent from
the candidates, or duplicate numbers disagree on text.

**Cost control:** every node touching an image uses the cheap model. `reconcile` — the only
expensive call — is **text-only over the candidate JSON**, never images. Confidence is capped
by source: marking scheme 0.7, worksheet submissions 0.85 (question images are uncapped).
All submission images go in a **single** multi-image call, not one call per file.

### Three details that matter

**Images never enter graph state.** State carries ids only. The service reads each upload
once, downscales to a 1600px long edge with Pillow (already a dependency), base64-encodes
**once**, and passes the `ImageBundle` through `config["configurable"]`, which LangGraph
passes by reference and never checkpoints. Rule to keep: *nothing base64 goes in
`RawHomeworkState`.* Downscaling is the single biggest token saving here — a 4000px phone
photo costs several times a 1600px one for identical extraction on printed worksheets.

**Token usage across nodes** uses a state reducer, not mutation:
`usage: Annotated[dict, add_usage]`. Each node returns a *delta*; LangGraph folds it in.
Plain `state["usage"] += x` raises `InvalidUpdateError` when branches run in parallel.
`usage_from_ai_message()` maps LangChain's `input_tokens`/`output_tokens` onto the repo's
existing `prompt_tokens`/`completion_tokens` names. Requires
`with_structured_output(..., include_raw=True)` — without it the raw `AIMessage` and its
`usage_metadata` are discarded.

**Structured output is not guaranteed.** Qwen3-VL 8B/32B/235B and 30B-A3B-Thinking all
advertise `response_format: json_schema` on OpenRouter, but support varies by which provider
OpenRouter routes to, and that rotates. Mitigation: send
`extra_body={"provider": {"require_parameters": True}}` so OpenRouter only routes to
providers supporting the requested params, backed by a three-rung ladder —
`json_schema` → `json_mode` → prose + the salvaged tolerant parser — with the working mode
cached per model per process. Keep the structured-output schemas flat: no `anyOf`, no nested
`$defs` beyond one level.

**Do not read `cfg/free_models.cfg`** for this agent — its default `openrouter/free` routes
to arbitrary models that ignore JSON instructions and are often not multimodal at all. Pin
model ids in `llm.py`, overridable via `OPENROUTER_VL_MODEL` / `OPENROUTER_VL_THINKING_MODEL`.

### Files

New shared helpers (fills the currently empty `src/common/`):
- `src/common/images.py` — `LoadedImage`, `ImageBundle.content_parts(ids)`, `sniff_mime()`,
  `downscale_and_encode()`. The only base64 path in the backend.
- `src/common/llm_usage.py` — `EMPTY_USAGE`, `add_usage()` reducer, `usage_from_ai_message()`.
- `src/common/json_extract.py` — salvaged from `OpenRouterLLM.py`.

New agent package `src/ai_agents/raw_homework_processing/`:
`agent.py` (facade, builds `_meta`), `graph.py`, `state.py`, `schemas.py`, `prompts.py`,
`llm.py` (tier→model map, structured-output ladder), `filters.py` (regex filter parsing, no
LLM), and `nodes/` — one file per node above.

New HTTP module `src/modules/raw_homework_processing/` — controller, service,
`pydantic_model/`. Follows the `src/modules/class/class_controller.py:25-32` precedent
(`get_x_service()` + `Depends` + `response_model=`), not the inline-service style.

Every module uses the try/except logger shim from `OpenRouterLLM.py:8-13` so it works both
under FastAPI (`src.ai_agents.…`) and standalone with `PYTHONPATH=src`.

### Endpoint

```
POST /raw-homework/process      (multipart/form-data)
  submissions:            List[UploadFile]   required, 1..n
  question_images:        List[UploadFile]   optional
  marking_scheme_images:  List[UploadFile]   optional
  question_text:          str                optional
  marking_scheme_text:    str                optional
  question_text_role_hint: str = "auto"      auto | filter | questions
```

Registered in `src/main.py` next to line 27 (import) and line 86 (`include_router`), plus an
`openapi_tags` entry at lines 59-65. Identity via `request.state.user.get("sub")` — **do not**
wrap in `UUID()`, the `DEBUG_TOKEN` bypass returns the non-UUID `"debug-user"`.

Service-layer validation before any encoding: drop zero-byte parts (Swagger UI sends an empty
file part for optional `List[UploadFile]` fields — without this a phantom image reaches the
graph), allow only png/jpeg/webp by magic-byte sniff, reject HEIC with a clear 415, cap ~10 MB
per image / ~40 MB total / 20 images.

## Dependencies

`requirements.txt` — append: `python-multipart`, `langchain-core`, `langchain-openai`,
`langgraph`. Add `requirements-dev.txt` with `pytest`, `pytest-asyncio` (currently pytest
exists only inside the tox env, so tests can't run outside tox).

`.env.example` — add `OPENROUTER_VL_MODEL`, `OPENROUTER_VL_THINKING_MODEL`,
`LANGSMITH_TRACING=false` (langgraph pulls langsmith transitively; don't let telemetry leave
by accident).

`tox.ini` — two envs modelled on `[testenv:openrouter]` (lines 61-82): `rawhomework`
(offline, dummy key, no network) and `rawhomework-live` (`passenv OPENROUTER_API_KEY`).

## Verification

**Environment first — three blockers, all currently unmet:**
1. **WSL DNS is dead.** `getent hosts` fails for *every* host against resolver
   `10.255.255.254`; this blocks Supabase and Google Vision too. Fix with `wsl --shutdown`
   from Windows PowerShell. Verify with `getent hosts openrouter.ai` before anything else.
2. `OPENROUTER_API_KEY` is not in `.env` (placeholder is in `.env.example`).
3. No OpenRouter credits — every Qwen3-VL model is paid. Top up ≥ $15 (the 5.5% fee has a
   $0.80 floor, so smaller top-ups pay a 16% effective rate).

**Offline — the bulk of the testing, no API key, no network.** Nodes never construct a model;
`llm.py` exposes a factory injected through `config["configurable"]["llms"]`, so tests pass a
`FakeStructuredCaller` with a scripted list of `(schema_instance, usage_delta)`. No
monkeypatching. Add `src/tests/conftest.py` for the `sys.path` bootstrap.
- routing matrix via `graph.astream(..., stream_mode="updates")`, asserting which nodes ran:
  question-images-only skips the scheme and submission nodes; `question_text` as questions runs
  **no** VL node at all; worksheet-only submissions yield questions with confidence ≤ 0.85;
  answer-only submissions produce `error.code == "NO_QUESTIONS_FOUND"` **without raising**
- `filters.py` unit tests: `"only 5, 6 required"`, `"Q5 and Q6"`, `"5-8"`, `"do all"`, and
  `"Find angle POQ."` which must *not* parse as a filter
- usage: `add_usage` unit tests incl. `None` operands, then end-to-end asserting
  `_meta["usage"]["total_tokens"]` equals the scripted sum; plus an error-path test proving
  usage is still nested under `_meta`
- service layer called **directly** with `UploadFile`s wrapping `src/tests/ocrs/assets/ocr_math.png`
  — not through `TestClient`, which would trigger the lifespan at `src/main.py:43-49` and try
  to connect Prisma

**Live smoke — one call, answers what offline cannot:** does `qwen/qwen3-vl-32b-instruct`
actually honour `response_format: json_schema` today, and which rung of the ladder was used?
Print it. Then compare the two reconciliation models on one ambiguous case before committing
to the thinking tier.

**Fixtures — the two on disk happen to test both branches of the worksheet classifier:**
`ocr_math.png` is a worksheet (printed question 7 with handwritten answers below) and must
yield questions with `source="submissions"`; `ocr_messy_handwriting.jpeg` is answer-only prose
and must yield none, driving `NO_QUESTIONS_FOUND`. A live check on `ocr_math.png` is also the
only way to confirm the model transcribes the printed stem rather than paraphrasing the
student's answer. No standalone question image or marking-scheme image exists yet — crop
`ocr_math.png` or supply real ones to exercise the primary path.

## Deferred

- No checkpointer in slice 1 (`graph.compile()` bare). Safe because images live in config,
  not state.
- Worst case is several sequential VL calls; set explicit per-call timeouts and a
  `recursion_limit`. A 202 + job-id pattern belongs in a later slice.
- `src/main.py:186-191` and `GoogleCloudVisionAPI.py:246-252` duplicate the same extension-based
  MIME dispatch; both could call the new `sniff_mime()`. Out of scope, but the helper exists.
