import importlib.util
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures"

_spec = importlib.util.spec_from_file_location("plugin", ROOT / "plugin" / "plugin.py")
plugin = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(plugin)


def fixture(name):
    return (FIXTURES / f"{name}.json").read_text()


@pytest.mark.parametrize(
    ("case", "expected"),
    [
        ("empty", set()),
        ("idle", set()),
        ("firefox_call", {"firefox"}),
        ("chrome_call", {"chrome"}),
        ("slack_huddle", {"slack"}),
        ("handy_only", {"handy"}),
    ],
)
def test_capturing_binaries_when_streams_listed_then_returns_their_binaries(case, expected):
    assert plugin.capturing_binaries(fixture(case)) == expected
