# Model hand-off: connecting the fine-tuned router

The fine-tuned router is trained, evaluated and ready. This note covers what the backend needs, what PR #7 has to change before it can merge, and how to check the connection end to end. How to call each prompt is in [router-integration.md](router-integration.md). This note doesn't repeat it.

## 1. What is ready

| Setting | Value |
|---|---|
| `TINKER_MODEL_PATH` (router) | `tinker://a3d6c2fd-cc7a-5817-bb0c-143d40cc924f:train:0/sampler_weights/000012` |
| Base model (guard check, search summary) | `Qwen/Qwen3.5-9B` (`BASE_MODEL`) |
| Renderer | `qwen3_5_disable_thinking` |
| Sampling | `temperature=0`, `max_tokens=MAX_TOKENS` (350), `stop=[stop_token_id(tokenizer)]` |
| Router prompt version | `e018ffbee7cc` (`FROZEN_ROUTER_PROMPT_VERSION`) |
| Checkpoint expiry | None. It stays available. |

The checkpoint only works with the prompt it was trained on. At startup, compare `router_prompt_version()` with `FROZEN_ROUTER_PROMPT_VERSION` and refuse to start in live mode if they differ.

Set `TINKER_API_KEY` and `TINKER_MODEL_PATH` in `api/.env` locally and in Render's environment for production. Never commit them.

Results on the sealed test set (32 questions, details in [training/runs/REPORT.md](../training/runs/REPORT.md)):

| | Base | Fine-tuned |
|---|---|---|
| Routing | 30/32 | 32/32 |
| AI answers within target length | 55% | 82% |
| Content-rule problems | 5 | 1 |

The test set is small, so treat the routing gain as two questions, not as "100% accurate".

## 2. What changed in the contract since PR #7 started

PR #7 branched from PR #3, and ten PRs have changed `contract/` since then.

| Was (PR #3) | Now (`main`) |
|---|---|
| Router returns `{fit, route, reason}`; `Fit` enum with `scope_nudge`, `context_request`, `split_request` | Router returns a route only: `AI`, `SEARCH` or `HUMAN`. **`Fit` no longer exists.** |
| Card text written separately by the base model | The router writes the route's fields itself: `answer`; `search_query`; `who_to_ask` + `suggested_question` |
| `only_out_there`, `do_this` on every card | Replaced by **`outdoor_action`** on every route |
| Scope nudge for trivia ("What is photosynthesis?") | No scope nudge. Any safe question is routed (photosynthesis → AI). |
| Missing place / two questions decided by the router | Decided by a separate **guard check** on the base model (`guard.py`): `ok`, `needs_detail`, `two_questions` |
| SEARCH shows links only | SEARCH shows links plus a grounded **summary and optional local tip** (`search_summary.py`), checked with `ungrounded_numbers` |
| Qwen3-8B | Qwen3.5-9B |

## 3. PR #7 review

The UI work, the SerpApi client, the safety-rule step, the 422 error format and the 60 s abort are good foundations. But the PR can't merge as it stands.

**Blockers**

1. **It breaks `main`.** `route_dto.py` imports `Fit` from `offscript_contract.router`, which no longer exists. Because the contract's `__init__.py` imports `route_dto`, every test in the repo, including contract and training tests, fails at import (15 collection errors on a test merge).
2. **The model is never called.** `services/pipeline.py` picks the route with keyword lists (`"where"` → SEARCH, `"regular"` → HUMAN, else AI). AGENTS.md B3 says never fall back to rules for routing, and B9 says the route must come from the real checkpoint in production.
3. **Results are hard-coded text shown as real answers.** `handlers/ai.py` and `handlers/human.py` return fixed templates chosen by keyword (for example, any question containing "bird" gets the same answer). That breaks B9: mock or rule-generated text must never look like model output.
4. **Guard states are keyword rules too.** `scope_nudge` ("photosynthesis", "who won"), `split_request` ("and where is") and `search_limitation` ("stale") are matched by keyword. Scope nudge no longer exists. The other two now come from the guard check and the search step.
5. **Old card fields.** `only_out_there` and `do_this` are in `route_dto.py`, `web/src/types/route.ts` and `ResultCard.tsx`. They should be `outdoor_action`.
6. **Tests lock in the old behaviour.** `test_integration_qa.py` expects R16–R18 to be `scope_nudge`. Under the current AGENTS.md they're AI, SEARCH and SEARCH.
7. **The TypeScript types are hand-written.** B5 says they must be generated from the contract's JSON Schema.

**Smaller issues**

- `safety.py` matches plain substrings with no word boundaries. None of our 152 training and test questions trigger it, but ordinary outdoor questions do: "issue" matches `sue`, "stargazing after dark" matches `after dark`, "physiotherapy" matches `therapy`, "water treatment plant" matches `treatment`, "emergency exit gate" matches `emergency`. Use `\b` word boundaries and narrower phrases such as "walk alone after dark".
- `handlers/search.py` puts the SerpApi error text in the user-facing `reason`. Log only the error code (B8) and show a plain message.
- `SerpApiClient` opens a new `httpx.AsyncClient` per call. B3 asks for one shared client per service.
- The safety rules also run on `context` when it is `"none"`. That's harmless, but clean it to `None` first.
- `mock_router.py` builds its own fake answers. Mock mode should replay `contract/fixtures/router/`, `guard/` and `search_summary/` through the real parsers, and the UI must label it **MOCK** (router-integration.md, "Mocks").
- The pipeline has no 60 s budget, no single retry on network errors and no 503/504 mapping yet.

**Worth keeping:** the frontend screens and styles, `client.ts` error handling and abort, `SerpApiClient` (with a shared client), the safety-rule step (with word boundaries) and the 422 handler.

## 4. Suggested rebuild

Rebuild PR #7 on the current `main` rather than merging it. Keep the parts listed above and replace the routing and content parts.

1. **Response shapes (backend-led, still open in AGENTS.md B12).** Define the result, guard and error shapes for `POST /api/route` in `contract/`, built on `AIOutput`, `SearchOutput` and `HumanOutput` (including `outdoor_action`). Agree them with the model owner before coding, export JSON Schema and generate the TypeScript types.
2. **Tinker client module.** At startup, create two sampling clients: base (`BASE_MODEL`) for the guard check and summary, and tuned (`TINKER_MODEL_PATH`) for the router. Get the tokenizer once with the sampling client's `get_tokenizer()`. Check the prompt version as described in section 1. Inject the clients through FastAPI dependencies so tests use fakes.
3. **Pipeline**, in this order: `normalize_input` → safety rules → guard check → router → for SEARCH, SerpApi then summary → validate → respond with `request_id` and `latency_ms`. Each model call uses the build, render, sample, decode and parse helpers in router-integration.md.
4. **Failures.** Retry once on a network error or timeout, if the 60 s budget allows; never retry a parse error. Map failures to 502, 503 and 504 with honest messages, and never fall back to a default route.
5. **Mock mode.** `OFFSCRIPT_MODE=mock` replays the contract fixtures through the same parsers and is labelled MOCK. The API already refuses to start in production with mock on.
6. **Frontend.** Show `outdoor_action` on every route, the "Go offscript" step for HUMAN, the search summary, links and local tip for SEARCH, and the guard check's message.

## 5. How to check it works

Run these in order. Each one must pass before the next.

| Check | Command or step | Proves |
|---|---|---|
| Contract and unit tests | `make test` | Schemas, parsers, prompts and fixtures agree; fake clients exercise every pipeline branch |
| Lint | `make lint` | Types and style |
| Prompt parity | `make test-live` (needs a Tinker key in `training/.env`) | The contract's prompt rendering matches what the model was trained on, token for token |
| Health | `make dev-api`, then `make health` | `model_configured: true` once both Tinker env vars are set |
| Golden check | Send each question in `training/runs/sft-v1/golden/input.jsonl` to `POST /api/route` | See below |
| Phone check | `make dev`, open the app at 390 px width | One result per question, no mock label, honest errors |

**Golden check.** `training/runs/sft-v1/golden/raw_outputs.jsonl` holds the fine-tuned router's real replies to the AGENTS.md reference cases R01–R18 and R24 (never the sealed set). At temperature 0 the live backend should return the **same route** for each one, and usually the same text. A different route means the prompt, renderer or input cleanup doesn't match training. Check the prompt version first.

The golden run got 18 of 19 as expected. **R01 is a known model error:** "I want to join a casual game at the campus court. How should I ask?" should be AI (generic etiquette) but the router returns HUMAN. Match the recorded reply, and don't patch it with a rule.

These golden questions skip the guard check. In the full pipeline, R06, R17, R18 and R24 may stop at the guard check for missing detail (no area, match or event named). That's expected.

## 6. Known limitations

- **R01**: the boundary between "how to ask" (AI) and "local norms" (HUMAN) isn't perfect.
- **Vague questions**: when the question has no name or place, the router can write a placeholder query, as R24 did (`[event name] confirmed happening today`). The guard check should stop these first.
- **General questions**: the outdoor action can be weak for questions with nothing to do outside, as R17 shows ("look for its official result online").
- **One sealed failure**: one HUMAN question still says "right now" (s029), which implies someone is present.
