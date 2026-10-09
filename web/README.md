# web/

React + Vite + TypeScript (strict) frontend. It has one page with no routing library.

```
src/
  app/                 state machine: idle → loading → card | guard | error → pocket → return
  screens/             Ask, Loading, Result, Pocket, Return
  components/          FieldCard (+ AI/SEARCH/HUMAN variants), GuardCard, ErrorCard
  api/                 fetch client (60 s abort)
  contract/generated/  TS types generated from contract/ (never hand-edit)
  lib/                 localStorage helpers (return notes, try/catch)
  styles/
tests/                 Vitest
e2e/                   Playwright (390 px, 1280 px)
```

Setup: copy `.env.example` to `.env.local`, then run `make dev-web` from the repo root. The scaffold page shows live `/health` status from the API. Rules: AGENTS.md B7.
