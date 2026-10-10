"""Qwen3.5 chat prompt rendering without tinker-cookbook (and therefore without PyTorch).

Mirrors the cookbook's `qwen3_5_disable_thinking` renderer token for token: message content is
stripped of leading/trailing whitespace (as Qwen3.5's template does), headers and the generation
suffix are encoded as fixed text, and content with `split_special_tokens=True` so a user typing
"<|im_end|>" gets plain text, not a control token. A live test checks parity with the cookbook.
"""

from typing import Protocol

from offscript_contract.router import STOP_TOKEN

ALLOWED_ROLES = ("system", "user")
GENERATION_SUFFIX = "<|im_start|>assistant\n<think>\n\n</think>\n\n"


class Tokenizer(Protocol):
    def encode(self, text: str, **kwargs: object) -> list[int]: ...

    def decode(self, tokens: list[int], **kwargs: object) -> str: ...


def stop_token_id(tokenizer: Tokenizer) -> int:
    tokens = tokenizer.encode(STOP_TOKEN, add_special_tokens=False)
    if len(tokens) != 1:
        raise ValueError(f"{STOP_TOKEN} must be a single token, got {tokens}")
    return tokens[0]


def render_chat_text(messages: list[dict[str, str]]) -> str:
    """The prompt as text, for snapshots and debugging. Not safe to tokenize directly."""
    parts = [
        f"{chr(10) if index else ''}<|im_start|>{message['role']}\n{message['content'].strip()}"
        f"{STOP_TOKEN}"
        for index, message in enumerate(messages)
    ]
    return "".join(parts) + "\n" + GENERATION_SUFFIX


def render_chat_prompt(tokenizer: Tokenizer, messages: list[dict[str, str]]) -> list[int]:
    """Token IDs for a system/user conversation, ending where the assistant reply starts."""
    if not messages:
        raise ValueError("messages must not be empty")
    end = stop_token_id(tokenizer)
    tokens: list[int] = []
    for index, message in enumerate(messages):
        role, content = message["role"], message["content"].strip()
        if role not in ALLOWED_ROLES:
            raise ValueError(f"role must be one of {ALLOWED_ROLES}, got {role!r}")
        header = f"{chr(10) if index else ''}<|im_start|>{role}\n"
        tokens += tokenizer.encode(header, add_special_tokens=False)
        tokens += tokenizer.encode(content, add_special_tokens=False, split_special_tokens=True)
        tokens.append(end)
    tokens += tokenizer.encode("\n" + GENERATION_SUFFIX, add_special_tokens=False)
    return tokens


def decode_completion(tokenizer: Tokenizer, tokens: list[int]) -> tuple[str, bool]:
    """Reply text up to the stop token, and whether the stop token was reached.

    `complete=False` means the model hit the token limit; pass it to parse_router_output.
    """
    end = stop_token_id(tokenizer)
    complete = end in tokens
    if complete:
        tokens = tokens[: tokens.index(end)]
    return tokenizer.decode(tokens), complete
