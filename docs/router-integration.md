# Router integration (backend)

How the API calls the tuned router so that it sees exactly what it was trained on. Everything named here lives in `contract/src/offscript_contract/`. Use it; don't reimplement it.

## What the router returns

```json
{"fit": "ok" | "scope_nudge" | "context_request" | "split_request",
 "route": "AI" | "SEARCH" | "HUMAN" | null,
 "reason": "one short sentence"}
```

`route` is set exactly when `fit` is `"ok"`. Parse with `parse_router_output`; never write a separate parser or model.

## Calling it

| Step | Use |
|---|---|
| Validate input | `normalize_input(question, context)`. Raises `InputError` with `code` (`question_empty`, `question_too_long`, `context_too_long`): return 422 with its message. Limits are counted after cleanup, so the API and training agree. |
| Build messages | `build_router_messages(question, context)` |
| Tokenize | `render_chat_prompt(tokenizer, messages)` → `tinker.ModelInput.from_ints(...)` |
| Sample | `tinker.SamplingParams(max_tokens=MAX_TOKENS, temperature=TEMPERATURE, stop=[stop_token_id(tokenizer)])` |
| Decode | `decode_completion(tokenizer, sequence.tokens)` → `(text, complete)` |
| Parse | `parse_router_output(text, complete=complete)` |

At startup, once:

- Create the sampling client: `tinker.ServiceClient().create_sampling_client(model_path=TINKER_MODEL_PATH)`.
- Get the tokenizer from it: `sampling_client.get_tokenizer()`. A live test confirms it matches the training tokenizer.
- Log `router_prompt_version()` and the checkpoint path.

The backend needs `tinker`, not `tinker-cookbook`. The contract's rendering mirrors the cookbook's `qwen3_disable_thinking` renderer token for token (checked by `make test-live`), so PyTorch is never installed on Render.

## Pipeline order

1. Input validation, then safety and refusal rules. The model is never trained on safety questions, so they must not reach it.
2. Router call.
3. If `fit != "ok"`, return that guard (the backend owns the guard copy).
4. Route handler, then card validation.

`search_limitation` comes from the search step, not the router.

## Failures

| Failure | Response |
|---|---|
| Network error or timeout | Retry once if the request's 60 s budget allows, then 504 |
| `RouterOutputError` (any code) | `invalid_model_output`, **no retry**: at temperature 0 a retry returns the same text |
| Key rejected or checkpoint missing/deleted | 503 model unavailable |
| Any failure | Never fall back to a default route or to rules |

Log only `fit`, `route`, latency and error codes; never the question, context or model text.

## Card text calls

Base-model calls that write card text (AI answer, HUMAN `who_to_ask` and `suggested_question`) also build prompts with `render_chat_prompt`, so user text can never become a control token. Their prompts and output formats are defined separately.

## Mock router

Only when `OFFSCRIPT_MODE=mock` (the API refuses to start with mock in production). Take raw texts from `contract/fixtures/router/outputs.json` and pass them through `parse_router_output`, the same as the real model. Use the `invalid` cases to test error handling. Responses are labelled mock.

## Versions and handover

- A checkpoint is valid only with the system prompt it was trained on. Every handover gives **both** `TINKER_MODEL_PATH` and `router_prompt_version()`.
- The system prompt goes first and is identical on every call, so Tinker's cached-prefill discount applies. Never add per-request text before it.
- Golden check at integration: `fit` and `route` must match the evaluation output exactly; `reason` may differ in wording.
