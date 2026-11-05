# Part B — RawHomeworkProcessingAgent

> Part A is done (OpenRouterLLM stripped, JSON parsing moved to `src/common/json_extract.py`,
> dead `/ai/*` endpoints removed). This is the remaining work.

## Goal

Given whatever material a teacher uploads — submissions, optional question images, optional
question text, optional marking scheme — work out **which questions are to be marked** and
return a canonical question list for the marking agents that come later.

Response shape, filtered to required questions only:

```json
{"questions": [{"number": "5", "text": "Find angle POQ."}]}
```

`source` and `confidence` are tracked internally but never returned.

## Decisions already taken

| | |
|---|---|
| framework | LangGraph + LangChain |
| transport | FastAPI endpoint, multipart upload |
| extraction model | `qwen/qwen3-vl-32b-instruct` |
| reconciliation model | `qwen/qwen3-vl-30b-a3b-thinking` — one-line-swappable, to be compared live |
| submissions as a question source | yes, **only when the submission is a worksheet** |

**Worksheet rule.** Many submissions are worksheets: the question is *printed* on the page and
the student writes answers on it. That printed text is as readable as a question image. What is
not recoverable is a question from a blank sheet carrying only working.

| what the image shows | result |
|---|---|
| printed question text (**worksheet**) | extract number + text, confidence capped at 0.85 |
| only handwritten working | contributes nothing; if no other source yielded questions → `NO_QUESTIONS_FOUND` |

The prompt must say question text is transcribed **only where printed**, never inferred from a
student's answer. Mixed batch → union across worksheet-type submissions.

## Graph

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

decide_escalation → needs_escalation ? reconcile (thinking, TEXT-ONLY) : apply_filter
reconcile → apply_filter → finalize → END
```

`decide_escalation` is pure Python. It sets `needs_escalation` when candidates come from more
than one source, any confidence < 0.6, `required_numbers` contains a number absent from the
candidates, or duplicate numbers disagree on text.

**Cost control:** every node touching an image uses the cheap model. `reconcile` — the only
expensive call — is text-only over the candidate JSON, never images. Confidence capped by
source: marking scheme 0.7, worksheet submissions 0.85, question images uncapped. All
submission images go in a **single** multi-image call.

## Three things that will bite otherwise

**Images never enter graph state.** State carries ids only. The service reads each upload once,
downscales to a 1600px long edge with Pillow, base64-encodes **once**, and passes the
`ImageBundle` through `config["configurable"]` — passed by reference, never checkpointed.
Rule: *nothing base64 goes in `RawHomeworkState`.* Downscaling is the single biggest token
saving available.

**Token usage needs a reducer, not mutation.** `usage: Annotated[dict, add_usage]`; each node
returns a *delta* and LangGraph folds it in. `state["usage"] += x` raises `InvalidUpdateError`
when branches run in parallel. Requires `with_structured_output(..., include_raw=True)` —
without it the raw `AIMessage` and its `usage_metadata` are discarded.

**Structured output is not guaranteed.** Qwen3-VL 8B/32B/235B and 30B-A3B-Thinking all
advertise `response_format: json_schema`, but support depends on which provider OpenRouter
routes to, and that rotates. Send `extra_body={"provider": {"require_parameters": True}}` so
only capable providers are used, backed by a ladder: `json_schema` → `json_mode` → prose +
`src/common/json_extract.parse_json_response` (already built in Part A). Cache the working mode
per model per process. Keep schemas flat — no `anyOf`, no nested `$defs` beyond one level.

**Do not read `cfg/free_models.cfg`.** Its default `openrouter/free` routes to arbitrary models
that ignore JSON instructions and are often not multimodal. Pin ids in `llm.py`, overridable by
`OPENROUTER_VL_MODEL` / `OPENROUTER_VL_THINKING_MODEL`.

## Files

New shared helpers:
- `src/common/images.py` — `LoadedImage`, `ImageBundle.content_parts(ids)`, `sniff_mime()`,
  `downscale_and_encode()`. The only base64 path in the backend.
- `src/common/llm_usage.py` — `EMPTY_USAGE`, `add_usage()` reducer, `usage_from_ai_message()`
  (maps LangChain's `input_tokens`/`output_tokens` onto the repo's
  `prompt_tokens`/`completion_tokens`).

New agent package `src/ai_agents/raw_homework_processing/`: `agent.py` (facade, builds `_meta`),
`graph.py`, `state.py`, `schemas.py`, `prompts.py`, `llm.py`, `filters.py` (regex filter parsing,
no LLM), `nodes/` — one file per node.

New HTTP module `src/modules/raw_homework_processing/` — controller, service, `pydantic_model/`.
Follow `src/modules/class/class_controller.py:25-32` (`get_x_service()` + `Depends` +
`response_model=`), not the inline-service style.

Use the try/except logger shim from `OpenRouterLLM.py:8-13` so modules work under FastAPI and
standalone with `PYTHONPATH=src`.

## Endpoint

```
POST /raw-homework/process      (multipart/form-data)
  submissions:            List[UploadFile]   required, 1..n
  question_images:        List[UploadFile]   optional
  marking_scheme_images:  List[UploadFile]   optional
  question_text:          str                optional
  marking_scheme_text:    str                optional
  question_text_role_hint: str = "auto"      auto | filter | questions
```

Register in `src/main.py` (import near line 27, `include_router` near line 86, `openapi_tags`
at 59-65). Identity via `request.state.user.get("sub")` — **do not** wrap in `UUID()`, the
`DEBUG_TOKEN` bypass returns the non-UUID `"debug-user"`.

Service-layer validation before any encoding: drop zero-byte parts (Swagger UI sends an empty
file part for optional `List[UploadFile]` fields), allow only png/jpeg/webp by magic-byte sniff,
reject HEIC with a clear 415, cap ~10 MB per image / ~40 MB total / 20 images.

## Dependencies

Still to install: `python-multipart`, `langchain-openai`, `langgraph`.
(`langchain-core` 1.6.6 is already installed and in `requirements.txt` from Part A.)

Add `requirements-dev.txt` with `pytest`, `pytest-asyncio` — they currently exist only inside
the tox env, so tests can't run outside tox.

`.env.example` — add `OPENROUTER_VL_MODEL`, `OPENROUTER_VL_THINKING_MODEL`,
`LANGSMITH_TRACING=false` (langsmith arrived transitively with langchain-core; don't let
telemetry leave by accident).

`tox.ini` — two envs modelled on `[testenv:openrouter]` (lines 61-82): `rawhomework` (offline,
dummy key, no network) and `rawhomework-live` (`passenv OPENROUTER_API_KEY`).

## Verification

**Blockers:** `OPENROUTER_API_KEY` is not in `.env`, and the account has no credits — every
Qwen3-VL model is paid. Top up ≥ $15 (the 5.5% fee has a $0.80 floor). Network itself is fine
again; `openrouter.ai` resolves and returns 200.

**Offline — the bulk of it.** Nodes must never construct a model: `llm.py` exposes a factory
injected through `config["configurable"]["llms"]`, so tests pass a `FakeStructuredCaller` with a
scripted list of `(schema_instance, usage_delta)`. No monkeypatching. Add `src/tests/conftest.py`
for the `sys.path` bootstrap.

- routing matrix via `graph.astream(..., stream_mode="updates")`, asserting which nodes ran:
  question-images-only skips the scheme and submission nodes; `question_text` as questions runs
  **no** VL node at all; worksheet submissions yield confidence ≤ 0.85; answer-only submissions
  produce `error.code == "NO_QUESTIONS_FOUND"` **without raising**
- `filters.py`: `"only 5, 6 required"`, `"Q5 and Q6"`, `"5-8"`, `"do all"`, and
  `"Find angle POQ."` which must *not* parse as a filter
- usage: `add_usage` unit tests incl. `None` operands; end-to-end asserting
  `_meta["usage"]["total_tokens"]` equals the scripted sum; error path still nests under `_meta`
- service layer called **directly** with `UploadFile`s wrapping the fixtures — not through
  `TestClient`, which triggers the lifespan at `src/main.py:43-49` and tries to connect Prisma

**Live smoke — one call.** Does `qwen/qwen3-vl-32b-instruct` honour `response_format: json_schema`
today, and which rung of the ladder was used? Print it. Then compare both reconciliation models
on one ambiguous case before committing to the thinking tier.

**Fixtures** in `src/tests/ocrs/assets/` test both branches of the worksheet classifier:
`ocr_math.png` is a worksheet (printed question 7 + handwritten answers) and must yield questions
with `source="submissions"`; `ocr_messy_handwriting.jpeg` is answer-only prose and must yield
none. The live run on `ocr_math.png` is the only way to confirm the model *transcribes* the
printed stem rather than paraphrasing the student's answer. No standalone question image or
marking-scheme image exists yet — crop `ocr_math.png` or supply real ones.

## Deferred

- No checkpointer in slice 1 (`graph.compile()` bare). Safe because images live in config.
- Several sequential VL calls worst case — set explicit per-call timeouts and a
  `recursion_limit`. A 202 + job-id pattern belongs in a later slice.
- `src/main.py:186-191` and `GoogleCloudVisionAPI.py:246-252` duplicate the same extension-based
  MIME dispatch; both could call the new `sniff_mime()`.
