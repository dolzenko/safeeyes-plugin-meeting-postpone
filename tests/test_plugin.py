import importlib.util
import logging
import pathlib
import subprocess

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


def test_last_capture_time_when_listed_app_captures_then_returns_now():
    assert plugin.last_capture_time({"chrome"}, {"firefox", "chrome"}, previous=100.0, now=200.0) == 200.0


def test_last_capture_time_when_only_unlisted_app_captures_then_keeps_previous():
    assert plugin.last_capture_time({"handy"}, {"firefox", "chrome"}, previous=100.0, now=200.0) == 100.0


def test_meeting_running_when_capture_dropped_one_second_ago_then_true():
    assert plugin.meeting_running(last_capture=100.0, now=101.0)


def test_meeting_running_when_30_seconds_since_last_capture_then_false():
    assert not plugin.meeting_running(last_capture=100.0, now=130.0)


def test_meeting_running_when_no_capture_seen_then_false():
    assert not plugin.meeting_running(last_capture=None, now=100.0)


def _pactl_returning(stdout):
    def run(args, **kwargs):
        return subprocess.CompletedProcess(args, 0, stdout=stdout, stderr="")
    return run


def _pactl_raising(error):
    def run(args, **kwargs):
        raise error
    return run


def test_read_capturing_binaries_when_pactl_succeeds_then_returns_binaries():
    assert plugin.read_capturing_binaries(_pactl_returning(fixture("slack_huddle"))) == {"slack"}


@pytest.mark.parametrize(
    "run",
    [
        _pactl_returning("not json"),
        _pactl_returning('[{"no": "properties"}]'),
        _pactl_raising(FileNotFoundError("pactl")),
        _pactl_raising(subprocess.CalledProcessError(1, ["pactl"])),
        _pactl_raising(subprocess.TimeoutExpired(["pactl"], 5)),
    ],
)
def test_read_capturing_binaries_when_pactl_fails_then_returns_empty_set(run):
    assert plugin.read_capturing_binaries(run) == set()


def test_read_capturing_binaries_when_pactl_fails_then_logs_warning(caplog):
    with caplog.at_level(logging.WARNING):
        plugin.read_capturing_binaries(_pactl_returning("not json"))

    assert "pactl" in caplog.text
