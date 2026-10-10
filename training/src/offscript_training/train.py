"""LoRA fine-tuning of the router on Tinker with the cookbook's supervised trainer.

Writes the run to training/runs/<name>/: run_config.json (ours: model, prompt version, data,
settings), the cookbook's config.json, metrics.jsonl and checkpoints.jsonl (tinker:// paths, no
weights), and run_summary.json.

    uv run --env-file training/.env python -m offscript_training.train --name sft-v1
    uv run --env-file training/.env python -m offscript_training.train --name dry-run --max-steps 2
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

from tinker_cookbook import hyperparam_utils
from tinker_cookbook.renderers import TrainOnWhat
from tinker_cookbook.supervised import train
from tinker_cookbook.supervised.data import FromConversationFileBuilder
from tinker_cookbook.supervised.types import ChatDatasetBuilderCommonConfig

from offscript_contract.router import BASE_MODEL, RENDERER_NAME, router_prompt_version
from offscript_training.data import TRAIN_FILE, load_train, refuse_sealed, to_conversation

RUNS = Path("training/runs")
DEFAULTS = {
    "lora_rank": 32,
    "learning_rate": round(hyperparam_utils.get_lr(BASE_MODEL), 6),
    "lr_schedule": "linear",
    "num_epochs": 4,
    "batch_size": 16,
    "validation_rows": 15,
    "max_length": 2048,
    "seed": 0,
}


def build_config(name: str, train_file: Path, settings: dict, max_steps: int | None):
    refuse_sealed(train_file)
    run_dir = RUNS / name
    run_dir.mkdir(parents=True, exist_ok=True)
    examples = load_train(train_file)
    conversations = run_dir / "train_conversations.jsonl"
    with conversations.open("w", encoding="utf-8") as out:
        for example in examples:
            out.write(json.dumps(to_conversation(example), ensure_ascii=False) + "\n")
    record = {
        "base_model": BASE_MODEL,
        "renderer": RENDERER_NAME,
        "router_prompt_version": router_prompt_version(),
        "train_file": str(train_file),
        "train_rows": len(examples),
        "max_steps": max_steps,
        **settings,
    }
    (run_dir / "run_config.json").write_text(json.dumps(record, indent=2) + "\n")
    dataset = FromConversationFileBuilder(
        file_path=str(conversations),
        test_size=settings["validation_rows"],
        shuffle_seed=settings["seed"],
        common_config=ChatDatasetBuilderCommonConfig(
            model_name_for_tokenizer=BASE_MODEL,
            renderer_name=RENDERER_NAME,
            max_length=settings["max_length"],
            batch_size=settings["batch_size"],
            train_on_what=TrainOnWhat.LAST_ASSISTANT_MESSAGE,
        ),
    )
    config = train.Config(
        log_path=str(run_dir),
        model_name=BASE_MODEL,
        recipe_name="offscript_router_sft",
        renderer_name=RENDERER_NAME,
        dataset_builder=dataset,
        learning_rate=settings["learning_rate"],
        lr_schedule=settings["lr_schedule"],
        num_epochs=settings["num_epochs"],
        lora_rank=settings["lora_rank"],
        eval_every=3,
        save_every=6,
        # The real run's checkpoints must not expire (the app uses one); a dry run's may.
        ttl_seconds=24 * 3600 if max_steps else None,
        max_steps=max_steps,
    )
    return run_dir, config


def summarise(run_dir: Path) -> dict:
    """Final sampler checkpoint and last metrics, read from the cookbook's log files."""
    checkpoints = [
        json.loads(line)
        for line in (run_dir / "checkpoints.jsonl").read_text().splitlines()
        if line.strip()
    ]
    samplers = [c for c in checkpoints if c.get("sampler_path")]
    samplers.sort(key=lambda c: bool(c.get("final")))  # the final checkpoint wins if present
    metrics = [
        json.loads(line)
        for line in (run_dir / "metrics.jsonl").read_text().splitlines()
        if line.strip()
    ]
    summary = {
        "final_sampler_path": samplers[-1]["sampler_path"] if samplers else None,
        "checkpoints": checkpoints,
        "last_metrics": metrics[-1] if metrics else None,
    }
    (run_dir / "run_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--name", required=True, help="run folder under training/runs/")
    parser.add_argument("--train-file", type=Path, default=TRAIN_FILE)
    parser.add_argument("--max-steps", type=int, help="stop early (dry run)")
    for key, value in DEFAULTS.items():
        parser.add_argument(f"--{key.replace('_', '-')}", type=type(value), default=value)
    args = parser.parse_args(argv)
    settings = {key: getattr(args, key) for key in DEFAULTS}
    run_dir, config = build_config(args.name, args.train_file, settings, args.max_steps)
    if (run_dir / "metrics.jsonl").exists():
        print(f"{run_dir} already has a run; choose a new --name.")
        return 1
    asyncio.run(train.main(config))
    summary = summarise(run_dir)
    print(f"final sampler checkpoint: {summary['final_sampler_path']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
