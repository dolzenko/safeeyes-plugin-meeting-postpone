import importlib.util
import json
import logging
import pathlib
import subprocess
import types

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


class FakeClock:
    def __init__(self, now=1000.0):
        self.now = now

    def __call__(self):
        return self.now


def test_parse_meeting_apps_when_space_separated_then_returns_set():
    assert plugin.parse_meeting_apps("  firefox   zoom ") == {"firefox", "zoom"}


def test_monitor_when_listed_app_polled_then_meeting_running(monkeypatch):
    monkeypatch.setattr(plugin, "read_capturing_binaries", lambda: {"slack"})
    monitor = plugin.MeetingMonitor({"slack"}, clock=FakeClock())

    monitor.poll()

    assert monitor.is_meeting_running()


def test_monitor_when_app_added_to_list_then_counts_as_meeting(monkeypatch):
    monkeypatch.setattr(plugin, "read_capturing_binaries", lambda: {"zoom"})
    monitor = plugin.MeetingMonitor(plugin.parse_meeting_apps("firefox zoom"), clock=FakeClock())

    monitor.poll()

    assert monitor.is_meeting_running()


def test_monitor_when_grace_period_passes_then_meeting_not_running(monkeypatch):
    clock = FakeClock()
    reads = iter([{"chrome"}, set()])
    monkeypatch.setattr(plugin, "read_capturing_binaries", lambda: next(reads))
    monitor = plugin.MeetingMonitor({"chrome"}, clock=clock)
    monitor.poll()
    clock.now += plugin.GRACE_SECONDS

    monitor.poll()

    assert not monitor.is_meeting_running()


@pytest.fixture
def fresh_plugin(monkeypatch):
    monkeypatch.setattr(plugin, "read_capturing_binaries", lambda: set())
    monkeypatch.setattr(plugin, "_monitor", None)
    monkeypatch.setattr(plugin, "_thread", None)
    yield plugin
    plugin.on_exit()


def test_init_when_called_twice_then_one_polling_thread(fresh_plugin):
    fresh_plugin.init({}, {}, {"meeting_apps": "firefox"})
    first = fresh_plugin._thread

    fresh_plugin.init({}, {}, {"meeting_apps": "firefox"})

    assert fresh_plugin._thread is first and first.is_alive()


def test_init_when_called_again_then_updates_meeting_apps(fresh_plugin):
    fresh_plugin.init({}, {}, {"meeting_apps": "firefox"})

    fresh_plugin.init({}, {}, {"meeting_apps": "slack zoom"})

    assert fresh_plugin._monitor.meeting_apps == {"slack", "zoom"}


def test_init_when_setting_missing_then_uses_default_apps(fresh_plugin):
    fresh_plugin.init({}, {}, {})

    assert fresh_plugin._monitor.meeting_apps == {"firefox", "chrome", "chromium", "slack"}


def test_on_exit_when_thread_running_then_thread_stops(fresh_plugin):
    fresh_plugin.init({}, {}, {})
    thread = fresh_plugin._thread

    fresh_plugin.on_exit()
    thread.join(timeout=1)

    assert not thread.is_alive()


def test_init_when_called_right_after_disable_then_polling_resumes(fresh_plugin):
    fresh_plugin.init({}, {}, {})
    fresh_plugin.disable()

    fresh_plugin.init({}, {}, {})

    assert fresh_plugin._thread.is_alive() and not fresh_plugin._stop.is_set()


class StubMonitor:
    def __init__(self, running):
        self.running = running

    def is_meeting_running(self):
        return self.running


@pytest.fixture
def safeeyes_context(monkeypatch):
    ctx = types.SimpleNamespace(postponed=False)
    monkeypatch.setattr(plugin, "context", ctx)
    return ctx


def test_on_start_break_when_meeting_running_then_postpones(monkeypatch, safeeyes_context):
    monkeypatch.setattr(plugin, "_monitor", StubMonitor(running=True))

    plugin.on_start_break(None)

    assert safeeyes_context.postponed


def test_on_start_break_when_meeting_running_then_does_not_skip(monkeypatch, safeeyes_context):
    monkeypatch.setattr(plugin, "_monitor", StubMonitor(running=True))

    assert plugin.on_start_break(None) is False


def test_on_start_break_when_no_meeting_then_break_unchanged(monkeypatch, safeeyes_context):
    monkeypatch.setattr(plugin, "_monitor", StubMonitor(running=False))

    assert plugin.on_start_break(None) is False and not safeeyes_context.postponed


def test_on_start_break_when_monitor_not_started_then_break_unchanged(monkeypatch, safeeyes_context):
    monkeypatch.setattr(plugin, "_monitor", None)

    assert plugin.on_start_break(None) is False and not safeeyes_context.postponed



@pytest.fixture
def plugin_config():
    return json.loads((ROOT / "plugin" / "config.json").read_text())


def test_config_when_loaded_then_only_setting_is_meeting_apps(plugin_config):
    assert [s["id"] for s in plugin_config["settings"]] == ["meeting_apps"]


def test_config_when_loaded_then_meeting_apps_default_matches_plugin(plugin_config):
    assert plugin_config["settings"][0]["default"] == plugin.DEFAULT_MEETING_APPS


def test_config_when_loaded_then_declares_pactl(plugin_config):
    assert plugin_config["dependencies"]["shell_commands"] == ["pactl"]


def test_config_when_loaded_then_break_override_not_allowed(plugin_config):
    assert "break_override_allowed" not in plugin_config
