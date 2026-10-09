"""Tinker end-to-end smoke test: base sampling, a tiny LoRA SFT run, save, and tuned sampling.

Proves the account, credits, base model and SDK all work before real training starts.
It is a live check that costs a few cents, so it is never run in CI.

    uv run --env-file training/.env python -m offscript_training.smoke_test
"""

import asyncio
import os
import sys

import tinker
from tinker_cookbook import renderers
from tinker_cookbook.renderers import TrainOnWhat, get_text_content
from tinker_cookbook.supervised.common import compute_mean_nll
from tinker_cookbook.supervised.data import conversation_to_datum

from offscript_contract.router import BASE_MODEL
from offscript_contract.router import RENDERER_NAME as RENDERER

LORA_RANK = 16
STEPS = 5
LEARNING_RATE = 2e-4
CHECKPOINT_TTL_SECONDS = 24 * 3600  # throwaway checkpoint: auto-deleted after a day

# Placeholder prompt and labels to check the mechanics only; the real router prompt is in contract/.
SYSTEM_PROMPT = (
    'Reply only with JSON: {"fit": "ok"|"scope_nudge"|"context_request"|"split_request", '
    '"route": "AI"|"SEARCH"|"HUMAN"|null, "reason": "<one short sentence>"}'
)
EXAMPLES = [
    (
        "Question: What do regulars buy at this stall?\nContext: at the outdoor market",
        '{"fit":"ok","route":"HUMAN","reason":"Regulars know what is good here."}',
    ),
    (
        "Question: Is the museum open today? I want to visit.\nContext: none",
        '{"fit":"ok","route":"SEARCH","reason":"Opening hours change and need a live source."}',
    ),
    (
        "Question: What is photosynthesis?\nContext: none",
        '{"fit":"scope_nudge","route":null,"reason":"Fully answered on screen; no outing."}',
    ),
]


def conversation(user_message: str, answer: str | None = None) -> list[dict]:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]
    if answer is not None:
        messages.append({"role": "assistant", "content": answer})
    return messages


async def ask(sampler: tinker.SamplingClient, renderer, user_message: str) -> str:
    params = tinker.SamplingParams(
        max_tokens=150, temperature=0.0, stop=renderer.get_stop_sequences()
    )
    response = await sampler.sample_async(
        prompt=renderer.build_generation_prompt(conversation(user_message)),
        num_samples=1,
        sampling_params=params,
    )
    message, _ = renderer.parse_response(response.sequences[0].tokens)
    return get_text_content(message)


async def main() -> int:
    if not os.environ.get("TINKER_API_KEY"):
        print("FAIL: TINKER_API_KEY is not set. Put it in training/.env and pass --env-file.")
        return 1
    # Known failures get a plain message; anything unexpected keeps its full traceback.
    try:
        return await run()
    except tinker.AuthenticationError:
        print("FAIL: Tinker rejected the API key (401). Check TINKER_API_KEY in training/.env.")
    except tinker.PermissionDeniedError:
        print("FAIL: the key has no access (403). Check billing, credits or model access.")
    except (tinker.APIConnectionError, tinker.APITimeoutError):
        print("FAIL: could not reach Tinker (network error or timeout). Try again.")
    return 1


async def run() -> int:
    service = tinker.ServiceClient()
    probe = EXAMPLES[0][0]

    print(f"[1/4] Creating LoRA training client on {BASE_MODEL} (rank {LORA_RANK})")
    trainer = await service.create_lora_training_client_async(base_model=BASE_MODEL, rank=LORA_RANK)
    renderer = renderers.get_renderer(RENDERER, trainer.get_tokenizer(), model_name=BASE_MODEL)

    print("[2/4] Sampling the base model")
    base = await service.create_sampling_client_async(base_model=BASE_MODEL)
    print(f"      base: {await ask(base, renderer, probe)}")

    print(f"[3/4] Training {STEPS} steps on {len(EXAMPLES)} examples")
    data = [
        conversation_to_datum(
            conversation(user, answer),
            renderer,
            max_length=512,
            train_on_what=TrainOnWhat.LAST_ASSISTANT_MESSAGE,
        )
        for user, answer in EXAMPLES
    ]
    weights = [datum.loss_fn_inputs["weights"] for datum in data]
    for step in range(STEPS):
        fwd_bwd = await trainer.forward_backward_async(data, "cross_entropy")
        optim = await trainer.optim_step_async(tinker.AdamParams(learning_rate=LEARNING_RATE))
        result = await fwd_bwd.result_async()
        await optim.result_async()
        logprobs = [output["logprobs"] for output in result.loss_fn_outputs]
        print(f"      step {step}: loss {compute_mean_nll(logprobs, weights):.4f}")

    print("[4/4] Saving sampler weights and sampling the tuned model")
    saved = await trainer.save_weights_for_sampler_async(
        "smoke-test", ttl_seconds=CHECKPOINT_TTL_SECONDS
    )
    path = (await saved.result_async()).path
    print(f"      checkpoint: {path}")
    tuned = await service.create_sampling_client_async(model_path=path)
    print(f"      tuned: {await ask(tuned, renderer, probe)}")

    print("PASS: sampling, training, saving and checkpoint sampling all work.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
