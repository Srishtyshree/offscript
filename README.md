# Offscript

A mobile-first web app that turns a question about something you want to do nearby into the shortest useful path off the screen. A fine-tuned open-weight model picks one source (**AI**, **SEARCH** or **HUMAN**), and the app returns one short card with one real-world step.

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
