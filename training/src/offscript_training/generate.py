"""Fill in the missing training fields for the team's S06 rows with the base model, then filter.

For each source row (question, route, outdoor action) the base Qwen3.5-9B writes several
candidates for the route's fields. A candidate is kept only if the assembled router reply passes
the contract and the extra content rules below; the best one wins, and rows where nothing passes
are flagged for a person. The route and outdoor action always come from S06, never the model.

    uv run --env-file training/.env python -m offscript_training.generate \\
        training/data/s06_source.jsonl training/data/train_candidates.jsonl [--limit N]
"""

import argparse
import asyncio
import json
import sys
from importlib.resources import files
from pathlib import Path

import tinker

from offscript_contract.parsing import ModelOutputError, parse_model_json, word_count
from offscript_contract.rendering import decode_completion, render_chat_prompt, stop_token_id
from offscript_contract.router import (
    ANSWER_TARGET_WORDS,
    BASE_MODEL,
    ROUTER_OUTPUT,
    Route,
    clean_text,
)
from offscript_training.content_rules import content_problems

CANDIDATES = 4
TEMPERATURE = 0.7
MAX_TOKENS = 300
CONCURRENCY = 8
GENERATED = {
    Route.AI: ("reason", "answer"),
    Route.SEARCH: ("reason", "search_query"),
    Route.HUMAN: ("reason", "who_to_ask", "suggested_question"),
}


def load_prompt() -> str:
    return files("offscript_training").joinpath("prompts/generate_fields.md").read_text("utf-8")


def build_messages(row: dict) -> list[dict[str, str]]:
    user = (
        f"Route: {row['route']}\nQuestion: {clean_text(row['question'])}\n"
        f"Outdoor action: {clean_text(row['outdoor_action'])}"
    )
    return [{"role": "system", "content": load_prompt()}, {"role": "user", "content": user}]


def assemble(row: dict, text: str, complete: bool):
    """Parse one candidate into a full router reply, or raise ModelOutputError / ValueError."""
    from pydantic import TypeAdapter

    fields = parse_model_json(text, TypeAdapter(dict[str, str]), complete=complete)
    route = Route(row["route"])
    if set(fields) != set(GENERATED[route]):
        raise ValueError(f"expected fields {GENERATED[route]}, got {sorted(fields)}")
    payload = {"route": route.value, **fields, "outdoor_action": row["outdoor_action"]}
    return ROUTER_OUTPUT.validate_python(payload)


def pick_best(row: dict, candidates: list[tuple[str, bool]]) -> dict:
    """Keep candidates that pass everything; prefer AI answers closest to the target length."""
    passing, rejected = [], []
    for text, complete in candidates:
        try:
            reply = assemble(row, text, complete)
        except (ModelOutputError, ValueError) as error:
            rejected.append(str(error).splitlines()[0][:120])
            continue
        problems = content_problems(reply)
        if problems:
            rejected.append("; ".join(problems))
        else:
            passing.append(reply)
    result = {**row, "candidates_passing": len(passing), "rejected_reasons": rejected}
    if not passing:
        return {**result, "status": "flagged"}
    best = min(
        passing,
        key=lambda r: abs(word_count(r.answer) - ANSWER_TARGET_WORDS) if r.route is Route.AI else 0,
    )
    generated = {name: getattr(best, name) for name in GENERATED[best.route]}
    return {**result, **generated, "status": "generated"}


async def generate(rows: list[dict]) -> list[dict]:
    client = await tinker.ServiceClient().create_sampling_client_async(base_model=BASE_MODEL)
    tokenizer = client.get_tokenizer()
    params = tinker.SamplingParams(
        max_tokens=MAX_TOKENS, temperature=TEMPERATURE, stop=[stop_token_id(tokenizer)]
    )
    gate = asyncio.Semaphore(CONCURRENCY)

    async def one(row: dict) -> dict:
        prompt = tinker.ModelInput.from_ints(render_chat_prompt(tokenizer, build_messages(row)))
        async with gate:
            response = await client.sample_async(
                prompt=prompt, num_samples=CANDIDATES, sampling_params=params
            )
        return pick_best(row, [decode_completion(tokenizer, s.tokens) for s in response.sequences])

    return await asyncio.gather(*(one(row) for row in rows))


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--limit", type=int, help="only the first N rows of each route")
    args = parser.parse_args(argv)
    if "test_sealed" in args.source.name:
        print("Refusing to generate from the sealed test set.")
        return 1
    rows = [json.loads(line) for line in args.source.read_text("utf-8").splitlines() if line]
    if args.limit:
        rows = [
            r for route in Route for r in [x for x in rows if x["route"] == route][: args.limit]
        ]
    results = asyncio.run(generate(rows))
    with args.output.open("w", encoding="utf-8") as out:
        for result in results:
            out.write(json.dumps(result, ensure_ascii=False) + "\n")
    flagged = sum(r["status"] == "flagged" for r in results)
    generated = len(results) - flagged
    print(f"{len(results)} rows → {generated} generated, {flagged} flagged → {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
