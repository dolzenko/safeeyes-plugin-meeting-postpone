import json
import logging
import subprocess
import time

from threading import Event, Lock, Thread

GRACE_SECONDS = 30
POLL_SECONDS = 5
DEFAULT_MEETING_APPS = "firefox chrome chromium slack"
PACTL_COMMAND = ["pactl", "-f", "json", "list", "source-outputs"]
PACTL_TIMEOUT_SECONDS = 5

context = None
_monitor = None
_thread = None
_stop = Event()


def init(ctx, safeeyes_config, plugin_config) -> None:
    global context, _monitor, _thread, _stop
    context = ctx
    meeting_apps = parse_meeting_apps(plugin_config.get("meeting_apps", DEFAULT_MEETING_APPS))
    if _monitor is None:
        _monitor = MeetingMonitor(meeting_apps)
    else:
        _monitor.meeting_apps = meeting_apps
    if _thread is None or not _thread.is_alive() or _stop.is_set():
        _stop = Event()
        _thread = Thread(
            target=_poll_until_stopped, args=(_stop,), name="meeting-monitor", daemon=True
        )
        _thread.start()


def on_start_break(break_obj) -> bool:
    if _monitor is not None and _monitor.is_meeting_running():
        logging.info("A meeting app is using the microphone. Postponing the break.")
        context.postponed = True
    return False


def on_exit() -> None:
    _stop.set()


def disable() -> None:
    _stop.set()


def _poll_until_stopped(stop: Event) -> None:
    while not stop.is_set():
        _monitor.poll()
        stop.wait(POLL_SECONDS)


def parse_meeting_apps(setting: str) -> set[str]:
    return set(setting.split())


def capturing_binaries(pactl_json: str) -> set[str]:
    return {
        binary
        for stream in json.loads(pactl_json)
        if (binary := stream["properties"].get("application.process.binary"))
    }


def read_capturing_binaries(run=subprocess.run) -> set[str]:
    try:
        result = run(
            PACTL_COMMAND,
            capture_output=True,
            text=True,
            check=True,
            timeout=PACTL_TIMEOUT_SECONDS,
        )
        return capturing_binaries(result.stdout)
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError) as error:
        logging.warning("Cannot read capture streams from pactl: %s", error)
        return set()


def last_capture_time(
    binaries: set[str], meeting_apps: set[str], previous: float | None, now: float
) -> float | None:
    return now if binaries & meeting_apps else previous


def meeting_running(
    last_capture: float | None, now: float, grace: float = GRACE_SECONDS
) -> bool:
    return last_capture is not None and now - last_capture < grace


class MeetingMonitor:
    def __init__(self, meeting_apps: set[str], clock=time.monotonic):
        self.meeting_apps = meeting_apps
        self._clock = clock
        self._last_capture = None
        self._lock = Lock()

    def poll(self) -> None:
        binaries = read_capturing_binaries()
        with self._lock:
            self._last_capture = last_capture_time(
                binaries, self.meeting_apps, self._last_capture, self._clock()
            )

    def is_meeting_running(self) -> bool:
        with self._lock:
            return meeting_running(self._last_capture, self._clock())
