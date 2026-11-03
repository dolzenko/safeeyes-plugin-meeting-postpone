# Design

## Context

The target is SafeEyes 3.5.0 on Linux with PipeWire and `pipewire-pulse`, so `pactl` is available. The plugin keeps the id `teams-do-not-disturb`, because the installed copy is a symlink at `~/.config/safeeyes/plugins/teams-do-not-disturb` and SafeEyes stores its settings under that id.

SafeEyes calls a plugin's `on_pre_break` and `on_start_break` hooks. Returning `True` from either one skips the break. In `core.py`, after `on_start_break` returns, SafeEyes checks `context.postponed`. If the field is set, SafeEyes clears it and runs the break again after `postpone_duration`, without a pre-break notification and without checking `allow_postpone`. That path runs whether or not strict mode is on.

The manual test results are in proposal.md under Why.

## Goals / Non-Goals

**Goals:**

- Keep the plugin a single small Python file with no dependencies outside the standard library and `pactl`.
- Make the detection logic testable without SafeEyes, PipeWire or a real call.

**Non-Goals:**

- Detecting meetings where the user never grants microphone access, such as listen-only webinars.
- Suppressing the first pre-break notification that appears during a meeting.
- Renaming the plugin id or the repository.

## Decisions

### Read capture streams with `pactl -f json list source-outputs`

Each source output carries `application.process.binary`. The manual test showed the values `firefox`, `chrome` and `slack`. The noise-canceling filter has no binary and shows up only as `node.name`, so it never matches the list.

Alternatives: `pw-dump` gives the same data, but as a much larger graph that is harder to filter. `wpctl status` has no machine-readable output. Browser extensions were the old design, and the proposal explains why they are dropped.

### Poll in a background thread, and keep the time of the last capture

A daemon thread runs `pactl` every 5 seconds and stores the monotonic time of the last poll that found a listed app capturing. A meeting is running if that time is less than 30 seconds old. The 30-second grace period needs a history of polls, so a check made only at break time cannot implement it.

Alternative: `pactl subscribe` pushes events as they happen, but the plugin would still have to query the stream list after each event. At a 5-second interval, a poll costs almost nothing, and it needs no event parsing.

`init` can run more than once, for example when settings reload. It updates the settings that the running thread reads, and it starts a thread only if none is running.

### Postpone from `on_start_break`, never skip

`on_start_break` sets `context.postponed = True` while a meeting is running, and returns `False`. `on_pre_break` always returns `False`, because the only thing it can do is skip, and a skip loses the break.

The plugin sets the attribute `context.postponed`, not `context["postponed"]`, because SafeEyes marks item access as soft-deprecated.

### Drop `break_override_allowed`

Because of that flag, SafeEyes loaded the old plugin and started its server even while the plugin was disabled. Without it, the plugin runs only when it is enabled.

### Keep detection functions separate from the SafeEyes hooks

Two pure functions take their inputs as arguments. The first turns `pactl` JSON into the set of capturing binaries. The second decides "meeting running" from the time of the last capture, the current time and the grace period. The hooks and the polling thread call these functions. Tests use `pytest`, with fixture JSON shaped like real `pactl` output.

## Risks / Trade-offs

- [`context.postponed` is an internal SafeEyes field, not a documented plugin API] → The manual test checks it after every SafeEyes upgrade. If a release removes the field, setting it does nothing and the break screen appears. That failure is visible, and it never hides a break.
- [A listed browser capturing the mic for something other than a meeting, such as a voice-note site, counts as a meeting] → Accepted. The break is postponed, not lost.
- [The first pre-break notification still appears during a meeting] → Accepted. It is a small desktop notification, not the break screen.
- [Up to 5 seconds pass between joining a call and the first detection] → A break that falls due inside those seconds is shown. This is rare, and you can avoid it by joining a few seconds early.

## Migration Plan

1. Pull the change. The symlinked install picks it up.
2. Restart SafeEyes, then enable the plugin in its settings.
3. Remove the Teams and Meet extensions from the browsers.
4. Run the manual test in `docs/manual-test.md`, then enable strict mode.

Rollback: check out the previous commit and restart SafeEyes.
