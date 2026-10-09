import pytest
from pydantic import ValidationError

from offscript_api.config import Settings


def test_mock_mode_is_refused_in_production():
    with pytest.raises(ValidationError, match="not allowed"):
        Settings(_env_file=None, offscript_env="production", offscript_mode="mock")


def test_startup_errors_never_show_keys():
    with pytest.raises(ValidationError) as error:
        Settings(
            _env_file=None,
            offscript_env="production",
            offscript_mode="mock",
            tinker_api_key="tml-secret-should-not-appear",
            serpapi_api_key="serp-secret-should-not-appear",
        )
    assert "should-not-appear" not in str(error.value)


@pytest.mark.parametrize(
    ("env", "mode"),
    [("development", "mock"), ("development", "live"), ("production", "live")],
)
def test_other_combinations_start(env, mode):
    settings = Settings(_env_file=None, offscript_env=env, offscript_mode=mode)
    assert (settings.offscript_env, settings.offscript_mode) == (env, mode)
