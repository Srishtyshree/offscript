# Offscript: AI that knows when to stop answering

> *This is a submission for the Hacktoberfest Open-Source AI Challenge Week 1: Touch Grass.*

## What I Built

We built Offscript, a mobile web app for questions that should lead you into the world around you. It is especially useful when you want to do something nearby, but the answer depends on a place or the people there.

Say you see a group playing football at a park and want to join. An AI cannot know whether that group welcomes newcomers. When we asked Offscript, it suggested asking a player: “Is there room for a newcomer in this game?” That gives you a way to walk over and find out for yourself.

The screen should be the shortest part of that experience. Offscript helps you take the next step, then leaves the conversation to you.

You can ask it general questions too. It answers those normally, and it can search when a current fact matters. It suggests a physical step when that step would actually help.

## Demo

**[Try Offscript](https://offscript-web.onrender.com)**

It is designed for a phone. Ask it about something you want to do nearby and see where it sends you next.

## Code

**[Offscript on GitHub](https://github.com/bhavishyaone/offscript)**

Built with [@bhavishyaone](https://github.com/bhavishyaone) and [@srishtyshree](https://github.com/Srishtyshree) ([@iNotSoCrisp](https://github.com/iNotSoCrisp)).

## How I Built It

The difficult part was deciding where an answer should come from. “When does this group usually play?” and “Can I join them right now?” might mention the same park and the same game, but they need different responses.

We fine-tuned the open-weight Qwen3.5-9B model with LoRA through Tinker. We trained it twice: first on a smaller question set, then on 1,085 examples covering nearby and general questions, different ways of asking them, and cases where an outdoor step would make no sense. The model chooses whether to answer, search, or direct the user to a person. It can include a physical action when one is useful.

The app uses React and TypeScript on the frontend and FastAPI on the backend. SerpApi provides current search results, and the app is deployed on Render.

In our 110-question offline check, the fine-tuned model chose the intended source for 110 questions, compared with 103 for the untuned model. Unnecessary physical steps fell from 9 to 1 across 41 questions where none was expected. An older 32-question check still found three misses, particularly around questions about specific venues. Both results are in the repository.

## Why Does Open Innovation Matter?

Offscript can fail in two very believable ways. It can confidently answer for people it has never met, or it can send someone outside when a short answer would have done the job. Either mistake makes the app less useful.

Using an open-weight model let us train that decision directly. We could write examples where the answer belongs to the model, to a current source, or to someone in the real world, then check whether training changed its choices. That gave us something more useful than a prompt telling an AI to encourage people to go outside.

The code, training material, and evaluations are public. Other people can inspect the choices we made, find cases we missed, and improve them. That is especially valuable for an app built around places and people our team cannot possibly know firsthand.

## My Agent Session

We did not record the build with DevRelay, so we do not have a session to embed. The repository has the code, training material, and evaluation results.

## Prize Categories

- **Best Use of Tinker**
- **Best Use of SerpApi**
- **Best Use of Render**

---

**Contributors and coding agents: read [AGENTS.md](AGENTS.md) first.**

## Repo layout

| Folder | What |
|---|---|
| `web/` | React + Vite + TypeScript frontend (Node, npm) |
| `api/` | FastAPI backend (Python, uv) |
| `contract/` | Shared schemas used by `api/`, `training/` and `web/` |
| `training/` | Datasets, Tinker fine-tuning and evaluation (offline) |
| `docs/` | Product and team docs |

## Model

| | |
|---|---|
| Base model | `Qwen/Qwen3.5-9B` on Tinker, LoRA fine-tune (rank 32) |
| Fine-tuned router (v2.1, live) | `tinker://7422f56a-258e-5e14-85ef-aa63b9100926:train:0/sampler_weights/000030` |
| Router prompt | `router_system_v2`, version `0fb9c7853868` (frozen; the checkpoint only works with this prompt) |
| Training data | 1,085 reviewed rows in 212 scenario families (`training/data/v2/router_v2.jsonl`) |
| Test data | 110 sealed questions (`training/data/test_sealed_v2.jsonl`), never used for training or prompt tuning |

Results on the v2 sealed set, same prompt and settings for both models:

| | Base | Fine-tuned v2.1 |
|---|---|---|
| Routing | 103/110 | 110/110 |
| Outdoor step shown when none was needed | 9 of 41 | 1 of 41 |
| AI answers within target length | 85% | 100% |
| SEARCH queries adding a place the user never gave (32-question place check) | — | 0 of 28 |

The test sets are small, so a difference of one or two questions is within noise. Full numbers and caveats: [training/runs/sft-v2.1/EVALUATION.md](training/runs/sft-v2.1/EVALUATION.md) and [training/runs/REPORT_V2_1.md](training/runs/REPORT_V2_1.md). The earlier v1 model (always gives an outdoor step) is described in [training/runs/REPORT.md](training/runs/REPORT.md). Backend hand-off: [docs/model-handoff.md](docs/model-handoff.md).

## Setup on macOS (from scratch)

Run each step in Terminal. Skip any tool that its check command shows you already have.

### 1. Xcode Command Line Tools (gives you `git` and `make`)

```bash
xcode-select --install
```

Check: `git --version && make --version`

### 2. Homebrew (Mac package manager)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

On Apple Silicon Macs (M1 and later), add Homebrew to your shell, then open a new Terminal window:

```bash
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

Check: `brew --version`

### 3. Node.js 20.19 or newer (for `web/`)

```bash
brew install node
```

Check: `node --version` (should print v20.19 or higher).
If you use nvm, run `nvm install && nvm use` in the repo instead. It reads `.nvmrc`.

### 4. uv (for the Python parts)

```bash
brew install uv
```

Check: `uv --version`

You don't need to install Python yourself. uv downloads the version pinned in `.python-version` (3.12) automatically.

### 5. Get the code and install dependencies

```bash
git clone https://github.com/bhavishyaone/offscript.git
cd offscript
cp api/.env.example api/.env
cp web/.env.example web/.env.local
make install
```

`make install` installs the Python packages (uv), the web packages (npm) and the git pre-commit hooks.

Leave the keys in `api/.env` blank to run the app locally. Put real Tinker or SerpApi keys **only** in `api/.env`, which is never committed.

### 6. Run it

```bash
make dev
```

| Server | Address |
|---|---|
| Backend (FastAPI) | http://localhost:8000 |
| Frontend (React) | http://localhost:5173 |

Open http://localhost:5173. The page should say **"API ok (v0.1.0) · model not configured"**. Press `Ctrl + C` to stop both servers.

## Everyday commands

Run from the repo root. `make help` lists them all.

| Command | What it does |
|---|---|
| `make dev` | Start backend and frontend together |
| `make dev-api` / `make dev-web` | Start only one side |
| `make health` | Check the running backend's `/health` |
| `make test` | Run all tests |
| `make lint` | Run all lint, format and type checks |
| `make format` | Auto-format all code |

Run `make lint` and `make test` before opening a PR. CI runs the same checks.

## Troubleshooting

**`SSL: CERTIFICATE_VERIFY_FAILED` on your first commit or `make install`.** Python installed from python.org doesn't trust macOS certificates until you run its setup script once (adjust the version to yours):

```bash
"/Applications/Python 3.12/Install Certificates.command"
```

**Port already in use.** Stop the other process, or run `make dev-api API_PORT=8001`. If you do, also set `VITE_API_BASE_URL` in `web/.env.local` to match.
