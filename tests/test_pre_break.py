import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest


spec = importlib.util.spec_from_file_location(
    "meeting_plugin", Path(__file__).resolve().parents[1] / "plugin/plugin.py"
)
plugin = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plugin)


@pytest.mark.parametrize("running", [True, False])
def test_pre_break_postpones_before_warning_plugins(monkeypatch, running):
    context = SimpleNamespace(postponed=False)
    monkeypatch.setattr(plugin, "context", context)
    monkeypatch.setattr(
        plugin, "_monitor", SimpleNamespace(is_meeting_running=lambda: running)
    )

    assert plugin.on_pre_break(None) is running
    assert context.postponed is running


def test_pre_break_allows_warnings_before_monitor_starts(monkeypatch):
    monkeypatch.setattr(plugin, "context", SimpleNamespace(postponed=False))
    monkeypatch.setattr(plugin, "_monitor", None)

    assert plugin.on_pre_break(None) is False
