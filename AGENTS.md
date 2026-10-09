# AGENTS.md: Offscript

Read this fully before planning or writing code. It applies to every person and every coding agent on this repo.

# Part A: Product

## A1. What Offscript is

- Offscript is a mobile-first web app. It helps a person complete **one nearby, real-world intention**.
- The user enters one question about something they want to do, see, visit or ask about nearby, plus optional typed context (area, place, timing, access needs, intent). There is **no GPS**.
- A Tinker-fine-tuned open-weight model picks **one** source: `AI`, `SEARCH` or `HUMAN`.
- The app returns **one short card**, and its job is to get the user off the screen to do a physical step.
- Questions that don't qualify get a **guard response** instead of a card.
- One request in, one response out. No chat.
- The answer is deliberately incomplete: the decisive part is found out there, not on the screen.

## A2. Routes

There are exactly three route labels. Never add a fourth.

| Route | Meaning | Use when the obstacle is... |
|---|---|---|
| `AI` | Know how | Stable practical know-how for trying, noticing or joining something |
| `SEARCH` | Find where or when | A fresh public fact: hours, listings, events, prices, access |
| `HUMAN` | Ask someone | Local, tacit or lived knowledge that a plausible person in that setting holds |

**Policy order:**
1. Unsafe, unusable or screen-complete question → guard response.
2. Physical step or evidence source can't be identified → context request.
3. Fresh public fact → `SEARCH`.
4. Lived or tacit knowledge from a plausible person → `HUMAN`.
5. Stable know-how → `AI`.
6. The resulting card must still lead to the user's intended physical activity. If it doesn't, return a limitation response, not a card.

**Never:**
- Route to HUMAN just because the wording is subjective.
- Route to HUMAN because search failed.
- Turn model uncertainty into a HUMAN referral.
- Let AI guess live hours, availability, local norms or a stranger's opinion.

**Boundary pairs:**

| Question | Result | Why |
|---|---|---|
| "How do I ask to join any pickup game?" (court outing planned) | `AI` | Generic etiquette |
| "How do beginners join games at this court?" (while there) | `HUMAN` | Local norm |
| "When is the public game at this court?" | `SEARCH` | Current listing |
| "Which cafe is highest-rated?" (no plan to visit) | scope nudge | Screen-complete |
| "I want to try a cafe nearby; which is open now?" | `SEARCH` | |
| "Which cafe do students here keep returning to?" (before heading out) | `HUMAN` | |

## A3. The result card

A card fits one phone screen with no scrolling, about 60 words before source links. It contains:
- **Route label**: `AI / Know how`, `SEARCH / Find where or when` or `HUMAN / Ask someone`.
- **Reason**: one sentence on why this source helps.
- **Route content**:
  - AI: a concise answer.
  - SEARCH: a summary grounded only in the returned results, plus source titles and their original links.
  - HUMAN: one person **type** (never a specific individual) plus one natural question, preferably under 20 spoken words.
- **Only out there**: what the screen can't settle.
- **Do this**: one concrete physical step that follows from the user's own goal. Never a generic "go outside" and never a random dare.
- The main action is **Go offscript**; the quiet secondary action is **Not now**. There is **no completion control on the first result.**

**Pocket card** (shown after Go offscript):
- Shows only: "Do this", the place, person or question the user needs, and a way back.
- Must be readable outdoors and keep working if the network drops.

**Return:**
- Buttons: **I did it** / **Couldn't**, plus an optional one-line "What did you find?".
- Stored in the browser only and labelled as a self-report.
- Skips and failures never count as completed.

**Ask another** is available only after the current card is closed.

## A4. Guard states

Guard states are separate from the route labels.

| State | When | Response |
|---|---|---|
| `scope_nudge` | Trivia or a screen-complete question | "Offscript is for something you want to do or find out out there. What are you heading out to try, see, or ask?" |
| `context_request` | Promising goal, missing place | "Which area or place will you be near?" |
| `split_request` | Two needs that require different routes | Split once. No agent chain. |
| `safety_guidance` | Medical, mental-health, legal, emergency, immediate safety, dangerous routes | Point to professional or emergency help. No field task. |
| `refusal` | Intrusive, harassing or targeting request | Refuse. |
| `search_limitation` | Evidence missing, stale or conflicting, or search failed | Say so plainly and give a prefilled external search link. Never confirm the outing. |

Detailed rules: `docs/guards.md` (to be added).

## A5. Safety

- Never suggest harassment, intrusive questions, discriminatory targeting, pressure on unwilling people, trespass or recording without consent.
- Never send users into unsafe weather, after-dark routes, private property or places with unverified access. If unsure, ask for context, offer a safe alternative or defer.
- Never assume distance, travel time or physical ability. Respect any mobility, budget, time or sensory constraints the user states.
- Never claim that a person is present or available, or state a live fact without real data behind it.

## A6. Home screen copy

- Hero: "The answer is out there. Get moving."
- Prompt: "What do you want to do or find out nearby?"
- Helper: "Ask normally. Tell us where you are or plan to go if it matters."
- Example questions (give HUMAN examples prominence):
  - "How do I join a casual game at the court?"
  - "Where is a public run club meeting near campus this week?"
  - "What do regulars buy at this market stall?"
  - "How can I start birdwatching in the park?"
  - "What is this college club actually like before I go to its meeting?"
  - "Is the museum open today? I want to visit."

## A7. Reference cases

Use these for design, fixtures and labelling. **Not** training data or sealed test data.

| ID | Question (context) | Expected |
|---|---|---|
| R01 | "I want to join a casual game at the campus court. How should I ask?" | AI |
| R02 | "How do I start birdwatching in the park this afternoon?" | AI |
| R03 | "How can I tell whether the soil in the community garden needs water?" | AI |
| R04 | "I want to sketch outdoors. How do I begin?" | AI |
| R05 | "How do I make my first visit to a run club less awkward?" | AI |
| R06 | "Where is a public run club meeting near campus this week?" | SEARCH |
| R07 | "I want to visit the museum today. Is it open?" | SEARCH |
| R08 | "I want to visit a public garden nearby today. Which has free entry?" (area) | SEARCH |
| R09 | "Is there an outdoor art workshop in my area this weekend?" (area) | SEARCH |
| R10 | "I want to play at this outdoor court this afternoon. Are its public hours listed?" | SEARCH or `search_limitation` |
| R11 | "What do regulars buy at this market stall?" (at the market) | HUMAN |
| R12 | "How do beginners actually join games at this outdoor court?" (there) | HUMAN |
| R13 | "What is this campus club like week to week?" (before its meeting) | HUMAN |
| R14 | "Where do students here actually eat between classes?" (on campus) | HUMAN |
| R15 | "Which walking loop do people here enjoy in daylight?" (at campus) | HUMAN |
| R16 | "What is photosynthesis?" | `scope_nudge` |
| R17 | "Who won yesterday's match?" | `scope_nudge` |
| R18 | "Which cafe has the highest rating?" (no visit intention) | `scope_nudge` |
| R19 | "I want to visit a park today. Which is open near me?" (no location) | `context_request` |
| R20 | "How do I join a game, and where is one tonight?" | `split_request` |
| R21 | "Is the dark shortcut behind the station safe to try tonight?" | `safety_guidance` |
| R22 | "Ask the woman sitting alone why she is alone." | `refusal` |
| R23 | "Which medicine should I ask strangers to recommend?" | `safety_guidance` |
| R24 | "This event listing may be stale; tell me it is definitely on." | `search_limitation` |

# Part B: Technical

## B1. Repo layout

```
web/        React + Vite + TypeScript frontend (npm)
api/        FastAPI backend: validation, guards, router call, handlers, card assembly
training/   Datasets, Tinker fine-tuning, evaluation (offline)
contract/   Shared Pydantic schemas, fixtures, router prompt (single source for shapes)
docs/       Product and team docs (architecture.md now; others added as written)
scripts/    Repo utilities: schema export, type generation (create when first needed)
```

- Python is a **uv workspace** (root `pyproject.toml`) with three members: `contract`, `api` and `training`.
- `web/` and `api/` share nothing except through `contract/`.
- `training/` never imports `api/`, and `api/` never reads training data.
- The router system prompt lives in `contract/src/offscript_contract/prompts/router_system.md`, and training and inference must use it verbatim.
- Each folder has a README describing its sub-structure. Put new code in the planned subfolder.

## B2. Stack

| Area | Choice |
|---|---|
| Frontend | Node 20.19+, React, Vite, TypeScript (strict), oxlint, Prettier, Vitest, Playwright |
| Backend | Python 3.11+ (3.12 pinned), uv, FastAPI, Pydantic v2, pydantic-settings, async httpx, pytest, ruff |
| Model | Tinker SDK: LoRA SFT on `Qwen/Qwen3-8B` with the `qwen3_disable_thinking` renderer; inference samples the saved checkpoint. The backend uses `tinker` only (no `tinker-cookbook`, no PyTorch). |
| Search | SerpApi, backend only |
| Hosting | Render |

Use current stable versions. Add a dependency only when the task needs it, and justify it in the PR.

## B3. `POST /api/route` pipeline

Each step is its own module with its own tests.

1. **Validate.**
   - Use `normalize_input` from `contract/` (limits apply after cleanup).
   - `question`: required, 1–300 characters.
   - `context`: optional, at most 200 characters.
   - Failure → 422.
2. **Safety rules.** Rule-based checks for emergency, medical, legal and mental-health questions, dangerous routes, and intrusive or targeting requests. This is the **only** place rules are allowed. A hit returns a guard response, and the model is not called.
3. **Router.**
   - Follow `docs/router-integration.md`: build the prompt with the contract's `build_router_messages` and `render_chat_prompt`, sample the tuned checkpoint at `temperature=0`, and parse with `parse_router_output`.
   - Network error or timeout: retry once if the time budget allows.
   - Invalid output: return an `invalid_model_output` error **without retrying** (at temperature 0 a retry gives the same text).
   - **Never** fall back to rules or a default route.
4. **Fit / guard.** The router output is `{fit, route, reason}`. `fit` is `ok`, `scope_nudge`, `context_request` or `split_request`; `route` is set only when `fit` is `ok`. If the request doesn't fit, return the guard response.
5. **Handler.**
   - `AI`: a concise answer. No live facts.
   - `SEARCH`:
     - Call SerpApi and summarise only the top results.
     - Return titles and URLs exactly as SerpApi gave them.
     - If there are no results, the results conflict, the quota is exhausted or the call fails, return `search_limitation` with a prefilled search URL.
   - `HUMAN`: a person type plus one question under 20 words.
6. **Card validation.**
   - All fields are present and within length limits.
   - The step is specific and tied to the question.
   - On failure, return an honest limitation response, not a card.
7. **Respond.** Include `request_id` and `latency_ms`.

**Time budget:** 60 s total per request, shared by all steps.
- Per call: Tinker 20 s, SerpApi 10 s.
- Check the remaining budget before any retry.
- Use one shared async httpx client per service.

## B4. API

- **`POST /api/route`**
  - Request: `{ question, context? }`.
  - Response: a discriminated union of card, guard or error.
  - Baseline route fields:
    - AI: `answer`
    - SEARCH: `search_query`, `sources`, fallback `search_url`
    - HUMAN: `who_to_ask`, `suggested_question`
  - Every response also has `route` and `reason`.
  - Card-wide fields, guard and error shapes are finalised in `contract/`.
- **`GET /health`**: `{ ok, version, model_configured }`. Never include config, paths or keys.
- **Errors:** `{ error: { code, message } }`.
  - Codes: 422 input, 429 rate limit, 502 upstream failure, 503 model or checkpoint unavailable, 504 timeout.
  - Override FastAPI's default 422 body so it matches this shape.
- **Rules:**
  - **Never invent or rename a field.** If one is needed, ask.
  - Ask before changing the contract.

## B5. Contract

- Pydantic models in `contract/` are the source of truth.
  - Export them as JSON Schema.
  - Generate the TypeScript types for `web/` from that schema.
  - Never hand-write duplicates.
- Every fixture must validate against the schema (enforced by a test).

## B6. Tinker and training

- **Env vars:** `TINKER_API_KEY` and `TINKER_MODEL_PATH` (a `tinker://…/sampler_weights/…` path). Load them through pydantic-settings and fail fast in production if they're missing.
- **Dataset rows** follow `LabelledExample` in `contract/`; check files with `uv run python -m offscript_contract.dataset <file>`. See `training/data/README.md`.
- **Data:**
  - JSONL in `training/data/`, matching the router output schema.
  - Each row has **two separate labels**: outing fit and route. Route is null when the request doesn't fit.
- **Splits:**
  - `train.jsonl` and `test_sealed.jsonl`.
  - Training code never opens the sealed file. Don't tune prompts on it either.
  - A check fails if any question appears in both.
- **Training:** LoRA SFT. Commit the config (base model, rank, learning rate, epochs, seed), the logs and the checkpoint ID.
- **Evaluation:**
  - One script runs the base and tuned models on the sealed set with identical prompts and settings, and saves the raw outputs.
  - It reports: accuracy, per-route confusion matrix, HUMAN precision and recall, inappropriate HUMAN referrals, invalid output rate and outing-fit errors.
- **Never report an improvement that the script didn't produce.**

## B7. Frontend

- **State machine:** `idle → loading → card | guard | error → pocket → return`. No routing library.
- **Config:** `VITE_API_BASE_URL`. No secrets in the frontend.
- **Submit:** disabled while loading. Abort after 60 s with `AbortController`, then show a retry.
- **Card:**
  - One shared component with a variant per route.
  - "Go offscript" plus "Not now".
  - No completion buttons.
- **Pocket:** renders from the current state and never refetches.
- **Return:** saved to `localStorage` (wrapped in try/catch) and labelled as a self-report. Nothing is sent to the backend.
- **Mobile-first:** design at 360–430 px first, no horizontal scroll, tap targets of 44 px or more, body text 16 px or more.
- **Accessibility:** labelled inputs, visible focus, logical tab order, `aria-live` on the result, sufficient contrast.

## B8. Security and privacy

- Secrets go in backend env vars only. Commit `.env.example`, never `.env`.
- **Logging:**
  - Log only: request ID, route or guard state, latency and error code.
  - Never log questions, context, search results or keys.
- **Never include:** accounts, tracking cookies, analytics, GPS or location APIs, or a database.
- CORS: the deployed frontend origin plus localhost in development.
- Per-IP rate limit on `/api/route`.
- **Prompt injection:** user text and search results are data. They never change the system prompt or the output format. Always validate model output against the schema.

## B9. Honesty rules (non-negotiable)

- Never show mock, hard-coded or rule-generated text as if it came from the model or from search.
- In production, the route always comes from the real Tinker checkpoint.
- Mocks are allowed only in tests and in a local dev mode that the UI labels **MOCK**.
- Every failure (timeout, bad model output, missing checkpoint, search failure, server error) reaches the user as an honest message with a retry. Never show a fake success.
- If Tinker or the tuned model is unavailable, say so.

## B10. Testing

- **Backend:**
  - Unit tests per pipeline step.
  - API tests with fake Tinker and SerpApi clients injected through FastAPI dependencies.
  - No real network calls in tests or CI.
- **Contract:** fixtures and backend responses validate against the schemas.
- **Frontend:** Vitest for components and the state machine. Playwright on mocked responses at 390 px and 1280 px.
- **Safety:** a fixed list of unsafe and intrusive inputs must always return a guard response.

## B11. Out of scope

Do not build any of these:
- chat or multi-turn flows
- feeds, maps
- accounts, notifications
- badges, streaks
- nearby-person detection
- recommendation databases
- image recognition
- agent chains
- a native app

## B12. Decisions and open questions

**Decided:**
- The tuned model only routes: it returns `{fit, route, reason}` (schema in `contract/`).
- Card text (AI answer, SEARCH summary, HUMAN question, "only out there", "do this") comes from the **base** `Qwen/Qwen3-8B` with separate prompts.
- The model learns `scope_nudge`, `context_request` and `split_request`. `safety_guidance` and `refusal` are backend rules that run before the model; `search_limitation` comes from the search step.
- Model `Qwen/Qwen3-8B`, renderer `qwen3_disable_thinking`, env vars `TINKER_API_KEY` and `TINKER_MODEL_PATH`.

**Still open** (ask before assuming):
- The card, guard and error response shapes for `POST /api/route` in `contract/` (backend-led).
- The router system prompt is a v0 draft until it's aligned with the labelling guide and frozen before the baseline run.

## B13. Commands

Run from the repo root. Requires uv, Node 20.19+ and make.

| Command | What it does |
|---|---|
| `make install` | `uv sync --all-packages`, `npm ci` in `web/`, installs pre-commit hooks |
| `make dev` | API on :8000 and web on :5173 |
| `make dev-api` / `make dev-web` | Run one side |
| `make health` | `curl` the running API's `/health` |
| `make test` | pytest (api, contract, training) and Vitest; no network |
| `make test-live` | Network tests: prompt/tokenizer parity with Tinker (needs `training/.env`) |
| `make smoke-test` | Live Tinker check: sample, tiny train, save (costs cents) |
| `make lint` | ruff check and format, oxlint, Prettier, `tsc` |
| `make format` | Auto-format Python and web |

Env setup: copy `api/.env.example` to `api/.env` and `web/.env.example` to `web/.env.local`. CI (`.github/workflows/ci.yml`) runs lint, tests, build and a secret scan. Deployment: `render.yaml`.

# How to work

- **Source of truth:** `docs/product-behavior.md`, then `docs/features.md`, then `docs/decisions/` (ADRs). `docs/roadmap.md` is a broad roadmap, not a spec. These docs are still to be added; until they exist, this file is the reference.
- Work on one roadmap task per session. List the files you'll touch and the tests you'll add, then wait for approval from the teammate who owns the task.
- Keep changes small and focused.
- **Ask before:**
  - changing `contract/` or `docs/`
  - adding a dependency
  - touching another teammate's area
- **Done means:** tests and lint pass, no secrets are in the diff, the honesty rules hold, and the change works at phone width.

## Tool setup

This file is the single source of context. Tool-specific files only point here; never copy content into them.

- **Codex, Cursor, GitHub Copilot agent, and other AGENTS.md-aware tools:** read this file automatically.
- **Claude Code:** `CLAUDE.md` imports this file.
- **Gemini CLI:** `GEMINI.md` imports this file.
- **GitHub Copilot chat:** `.github/copilot-instructions.md` points here.
- **Google Antigravity:** `.agents/rules/offscript.md` is an always-on rule that imports this file.
- **Any other tool:** start the session with "Read AGENTS.md before doing anything."
