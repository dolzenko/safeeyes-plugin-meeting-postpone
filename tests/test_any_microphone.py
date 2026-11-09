import importlib.util
import json
from pathlib import Path
import subprocess

import pytest


spec = importlib.util.spec_from_file_location(
    "meeting_plugin", Path(__file__).resolve().parents[1] / "plugin/plugin.py"
)
plugin = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plugin)


@pytest.mark.parametrize(
    "binary,corked,muted,source,expected",
    [
        ("firefox", False, False, "microphone", {"firefox"}),
        ("firefox-bin", False, True, "microphone", {"firefox-bin"}),
        ("zoom", False, True, "microphone", {"zoom"}),
        ("obs", False, False, "microphone", {"obs"}),
        ("dictation", False, False, "microphone", {"dictation"}),
        (None, False, True, "microphone", {"*"}),
        ("firefox-bin", True, True, "microphone", set()),
        ("obs", False, False, "speakers.monitor", set()),
        ("firefox", False, False, None, set()),
    ],
)
def test_wildcard_filters_active_microphones(binary, corked, muted, source, expected):
    captures = json.dumps([{
        "source": 1, "corked": corked, "mute": muted,
        "properties": {"application.process.binary": binary} if binary else {},
    }])
    sources = json.dumps([{"index": 1, "name": source}] if source else [])
    calls = []

    def run(args, **kwargs):
        calls.append(args[-1])
        assert kwargs["check"] and kwargs["timeout"] == plugin.PACTL_TIMEOUT_SECONDS
        return subprocess.CompletedProcess(
            args, 0, stdout=captures if args[-1] == "source-outputs" else sources
        )

    assert plugin.read_capturing_binaries(run, microphones_only=True) == expected
    assert calls == ["source-outputs", "sources"]


def test_wildcard_matches_unlisted_or_anonymous_capture():
    assert plugin.last_capture_time({"firefox-bin"}, {"*"}, 100.0, 200.0) == 200.0
    assert plugin.last_capture_time({"*"}, {"*"}, 100.0, 200.0) == 200.0
    assert plugin.last_capture_time(set(), {"*"}, 100.0, 200.0) == 100.0


def test_wildcard_monitor_uses_microphone_filter_and_preserves_grace(monkeypatch):
    state = {"now": 1000.0, "binaries": {"firefox-bin"}}

    def read(*, microphones_only):
        assert microphones_only
        return state["binaries"]

    monkeypatch.setattr(plugin, "read_capturing_binaries", read)
    monitor = plugin.MeetingMonitor({"*"}, clock=lambda: state["now"])
    monitor.poll()
    assert monitor.is_meeting_running()
    state["binaries"] = set()
    state["now"] += 29
    monitor.poll()
    assert monitor.is_meeting_running()
    state["now"] += 1
    monitor.poll()
    assert not monitor.is_meeting_running()


@pytest.mark.parametrize("failure", ["not json", FileNotFoundError("pactl"),
                                      subprocess.TimeoutExpired(["pactl"], 5)])
def test_sources_query_failure_is_logged_and_returns_empty(failure, caplog):
    def run(args, **kwargs):
        if args[-1] == "source-outputs":
            return subprocess.CompletedProcess(args, 0, stdout="[]")
        if isinstance(failure, Exception):
            raise failure
        return subprocess.CompletedProcess(args, 0, stdout=failure)

    assert plugin.read_capturing_binaries(run, microphones_only=True) == set()
    assert "Cannot read capture streams from pactl" in caplog.text
