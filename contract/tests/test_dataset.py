import json

import pytest

from offscript_contract.dataset import LabelledExample, main, validate_dataset

GOOD = {
    "id": "t001",
    "question": "What do regulars buy at this stall?",
    "context": "at the outdoor market",
    "fit": "ok",
    "route": "HUMAN",
    "reason": "Regulars know what is good here.",
}


def write_rows(tmp_path, rows):
    path = tmp_path / "data.jsonl"
    path.write_text(
        "".join(row if isinstance(row, str) else json.dumps(row) + "\n" for row in rows)
    )
    return path


def test_valid_row_and_helpers():
    example = LabelledExample.model_validate(GOOD)
    assert example.category == "HUMAN"
    assert example.router_input.context == "at the outdoor market"
    assert example.label.to_target_json().startswith('{"fit":"ok","route":"HUMAN"')


def test_empty_context_is_allowed():
    row = {**GOOD, "context": "", "fit": "scope_nudge", "route": None}
    assert LabelledExample.model_validate(row).category == "scope_nudge"


@pytest.mark.parametrize(
    "change",
    [
        {"id": "has space"},
        {"question": "  untrimmed question?"},
        {"question": "two\nlines?"},
        {"context": "none"},
        {"context": "at the  market"},
        {"route": None},
        {"fit": "scope_nudge"},
        {"route": "human"},
        {"reason": ""},
        {"question": ""},
        {"question": "x" * 301},
        {"extra": "field"},
    ],
)
def test_bad_rows_are_rejected(change):
    with pytest.raises(ValueError):
        LabelledExample.model_validate({**GOOD, **change})


def test_report_lists_every_problem_with_line_numbers(tmp_path):
    path = write_rows(
        tmp_path,
        [
            GOOD,
            {**GOOD, "id": "t002", "route": None},
            "not json\n",
            "\n",
            {**GOOD, "id": "t001", "question": "Another question here?"},
            {**GOOD, "id": "t003", "question": "what do regulars buy at this stall?"},
            {**GOOD, "id": "t004", "question": "Is the pool open today?", "route": "SEARCH"},
        ],
    )
    report = validate_dataset(path)
    assert len(report.examples) == 4
    joined = "\n".join(report.errors)
    assert "line 2:" in joined
    assert "line 3: not valid JSON" in joined
    assert "line 4: blank line" in joined
    assert "line 5: id 't001' repeats line 1" in joined
    assert "line 6: question repeats line 1" in joined
    assert report.counts == {"HUMAN": 3, "SEARCH": 1}


def test_cli_exit_codes(tmp_path, capsys):
    good = write_rows(tmp_path, [GOOD])
    assert main([str(good)]) == 0
    bad = tmp_path / "bad.jsonl"
    bad.write_text("not json\n")
    assert main([str(bad)]) == 1
    assert "not valid JSON" in capsys.readouterr().out
