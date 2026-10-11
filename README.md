# Offscript

**AI that knows when to get you off the screen.**

Offscript is a mobile web app for questions whose best answer may be a fact, a live source, or a real person. It is built especially for nearby experiences where firsthand knowledge matters. Ask about a place, a group, or something you want to do; Offscript helps you take the next step in the world instead of keeping you in an endless chat.

General questions work too. The app answers them directly or searches for current information. It suggests a physical step only when that step genuinely helps.

**[Try the live app](https://offscript-web-ksob.onrender.com/)** · **[View the architecture](docs/architecture.md)**

## How it works

A fine-tuned open-weight model chooses the source that fits the question:

| Route | When it fits | What you get |
| --- | --- | --- |
| **AI** | Stable knowledge the model can answer | A concise answer |
| **SEARCH** | Current or publicly verifiable information | A web-backed result with sources |
| **HUMAN** | Firsthand experience, local norms, or a person's permission | A type of person to approach and one natural question to ask |

For example, “What is the hostel food actually like at IIT Delhi?” needs a current student's experience. Offscript can suggest a question to ask that student; the conversation happens off screen. A question such as “What is photosynthesis?” gets an answer without a forced outdoor task.

The app accepts an optional typed location or situation for context. It does not need GPS. It shows one result for each question, with a brief reason for its choice. Safety checks run before routing, and unavailable search results are shown as a limitation rather than guessed.

## Built with

- **Frontend:** React, TypeScript, and Vite; designed for phones.
- **Backend:** FastAPI and a shared Pydantic contract for request and response shapes.
- **Model:** `Qwen/Qwen3.5-9B`, fine-tuned with LoRA through Tinker. The deployed router uses the v2.1 checkpoint.
- **Live information:** SerpApi supplies current search results and source links.
- **Hosting:** Render, configured in [render.yaml](render.yaml).

The backend exposes `POST /api/route` and `GET /health`. See [AGENTS.md](AGENTS.md) for the product rules and [docs/router-integration.md](docs/router-integration.md) for the model integration.

## Model and evaluation

The second training round used **1,085 reviewed examples** across nearby and general questions. On the 110-question sealed offline set, the v2.1 router selected the intended route for **110/110** questions. It added an unnecessary outdoor step on **1 of 41** questions where no step was expected.

These are offline results on a small test set, not a claim of perfect real-world accuracy. The datasets, methods, failure cases, and caveats are documented in [the v2.1 evaluation](training/runs/sft-v2.1/EVALUATION.md) and [the comparison report](training/runs/REPORT_V2_1.md).

## Run locally

You need Node.js 20.19+, [uv](https://docs.astral.sh/uv/), and `make`. Python 3.12 is pinned in `.python-version`.

From the repository root:

```bash
cp api/.env.example api/.env
cp web/.env.example web/.env.local
make install
```

Set `TINKER_API_KEY`, `TINKER_MODEL_PATH`, and `SERPAPI_API_KEY` in `api/.env` to use the live model and search. The frontend reads `VITE_API_BASE_URL` from `web/.env.local`; its example points to the local API. Keep credentials out of the frontend and out of Git.

```bash
make dev
```

Open **http://localhost:5173**. The API runs at **http://localhost:8000**. Without model credentials, the health endpoint can run, but live routing is unavailable.

## Development

| Command | Purpose |
| --- | --- |
| `make health` | Check the running API |
| `make test` | Run Python and frontend tests |
| `make lint` | Run lint, formatting, and type checks |
| `make format` | Format the code |

Run `make test` and `make lint` before opening a pull request. Read [AGENTS.md](AGENTS.md) before changing product behavior or code.

| Directory | Contents |
| --- | --- |
| [web/](web/) | Mobile frontend |
| [api/](api/) | API, guards, routing, and result assembly |
| [contract/](contract/) | Shared schemas and prompts |
| [training/](training/) | Data, fine-tuning, and evaluations |
| [docs/](docs/) | Architecture and implementation notes |

## Team

Built by [Bhavishya](https://github.com/bhavishyaone), [Srishty](https://github.com/Srishtyshree), and [Shubh](https://github.com/iNotSoCrisp).
