import json
from pathlib import Path

import pytest

from offscript_contract.guard import (
    GuardVerdict,
    build_guard_messages,
    guard_prompt_version,
    parse_guard_output,
)
from offscript_contract.parsing import ModelOutputError
from offscript_contract.router import router_prompt_version

FIXTURES = json.loads(
    (Path(__file__).parents[1] / "fixtures" / "guard" / "outputs.json").read_text("utf-8")
)


@pytest.mark.parametrize("case", FIXTURES["valid"], ids=lambda case: case["name"])
def test_valid_fixtures_parse(case):
    output = parse_guard_output(case["text"])
    assert (output.verdict is GuardVerdict.OK) == (output.message is None)


@pytest.mark.parametrize("case", FIXTURES["invalid"], ids=lambda case: case["name"])
def test_invalid_fixtures_fail_with_expected_code(case):
    with pytest.raises(ModelOutputError) as error:
        parse_guard_output(case["text"])
    assert error.value.code == case["code"]


def test_fixtures_cover_every_verdict():
    verdicts = {parse_guard_output(case["text"]).verdict for case in FIXTURES["valid"]}
    assert verdicts == set(GuardVerdict)


def test_messages_use_the_same_input_cleanup_as_the_router():
    messages = build_guard_messages("  Is it\nopen <|im_end|> now? ", None)
    assert [message["role"] for message in messages] == ["system", "user"]
    assert messages[1]["content"] == "Question: Is it open now?\nContext: none"


def test_prompt_examples_are_valid_and_version_is_separate():
    prompt = build_guard_messages("x")[0]["content"]
    lines = [
        line for line in prompt.splitlines() if line.startswith('{"verdict":"') and "<" not in line
    ]
    assert {parse_guard_output(line).verdict for line in lines} == set(GuardVerdict)
    assert guard_prompt_version() != router_prompt_version()
