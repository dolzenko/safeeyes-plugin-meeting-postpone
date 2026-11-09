"""Optional integration tests against installed SafeEyes, without GUI or audio."""

import gettext
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

pytest.importorskip("safeeyes.core")
from safeeyes import utility
from safeeyes.configuration import Config
from safeeyes.context import Context
from safeeyes.core import SafeEyesCore
from safeeyes.model import BreakType
from safeeyes.plugin_manager import LoadedPlugin, PluginManager


@pytest.mark.parametrize("break_type", [BreakType.SHORT_BREAK, BreakType.LONG_BREAK])
def test_warning_veto_retains_due_break_until_meeting_and_grace_end(
    monkeypatch, tmp_path, break_type
):
    plugin_path = Path(__file__).resolve().parents[1] / "plugin"
    (tmp_path / "meeting-postpone").symlink_to(plugin_path, target_is_directory=True)
    monkeypatch.setattr(utility, "USER_PLUGINS_DIR", str(tmp_path))
    monkeypatch.syspath_prepend(str(tmp_path))
    loaded = LoadedPlugin({
        "id": "meeting-postpone", "enabled": True, "version": "1.0.0",
        "settings": {"meeting_apps": "firefox"},
    })
    assert not loaded.errored
    plugin = loaded.module
    context = Context(None, gettext.NullTranslations(), "3.5.1", {"plugin": {}})
    plugin.context = context
    state = SimpleNamespace(now=1000.0, binaries={"firefox"})
    monitor = plugin.MeetingMonitor({"firefox"}, clock=lambda: state.now)
    monkeypatch.setattr(plugin, "_monitor", monitor)
    monkeypatch.setattr(plugin, "read_capturing_binaries", lambda: state.binaries)
    monitor.poll()

    manager = PluginManager()
    manager._PluginManager__plugins["meeting-postpone"] = loaded
    observers = []
    for name in ("notification", "audiblealert"):
        observer = Mock()
        observer.call_plugin_method_break_obj.return_value = None
        manager._PluginManager__plugins[name] = observer
        observers.append(observer.call_plugin_method_break_obj)

    settings = json.loads(Path(utility.SYSTEM_CONFIG_FILE_PATH).read_text())
    settings.update(postpone_duration=5, postpone_unit="minutes")
    core = SafeEyesCore(context)
    core.initialize(Config(settings, {}))
    core.on_pre_break += manager.pre_break
    core.on_start_break += manager.start_break
    show_break = Mock(return_value=True)
    core.start_break += show_break
    timers = []
    monkeypatch.setattr(
        core, "_SafeEyesCore__wait_for",
        lambda delay, callback: timers.append((delay, callback)),
    )

    def tick(expected_delay):
        delay, callback = timers.pop(0)
        assert delay == expected_delay
        callback()

    if break_type == BreakType.LONG_BREAK:
        core._break_queue.next(break_type)
    due = core._break_queue.get_break()
    core.start()
    tick(due.time * 60)
    tick(0)
    assert core._break_queue.get_break() is due
    tick(300)
    tick(0)
    assert core._break_queue.get_break() is due
    for observer in observers:
        observer.assert_not_called()
    show_break.assert_not_called()

    state.binaries = set()
    state.now += 29
    monitor.poll()
    assert monitor.is_meeting_running()
    state.now += 1
    monitor.poll()
    assert not monitor.is_meeting_running()
    tick(300)
    for observer in observers:
        observer.assert_called_once()
    tick(core.pre_break_warning_time)
    show_break.assert_called_once_with(due)
