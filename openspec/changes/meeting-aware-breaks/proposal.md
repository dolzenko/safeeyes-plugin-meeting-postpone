# Proposal

## Why

SafeEyes strict mode removes the option to skip a break. To use it, a break screen must never cover a meeting. Today nothing protects a meeting: the plugin is disabled, and its browser extensions report presence unreliably. The sources overwrite each other, a status never expires, an open tab after a call counts as a meeting, and each extension works in one browser only.

A manual test on 2026-11-03 showed a simpler signal works. A meeting app holds the microphone exactly while a call is running. It keeps holding it while muted in the app or with the keyboard, and it releases the mic when the call ends, even if the tab or app stays open. This held for Meet in Firefox and Chrome, Teams in Chrome, and a Slack huddle.

## What Changes

- Detect a meeting by checking, through PipeWire, whether an allowlisted app is capturing the microphone.
- Postpone a break that falls due during a meeting, and retry until the meeting ends, instead of skipping it.
- **BREAKING**: Remove the Chrome and Firefox extensions and the HTTP presence server on port 6776.
- **BREAKING**: Replace the ten per-presence-state settings with a list of meeting apps.
- Rename the plugin's display name and README to describe meetings in general, not Teams. The plugin id `teams-do-not-disturb` stays, so the existing install and SafeEyes config keep working.

## Capabilities

### New Capabilities

- `meeting-detection`: decides whether a meeting is running, from which apps capture the microphone.
- `break-postponement`: what SafeEyes does with a break that falls due while a meeting is running.

### Modified Capabilities

None. The project has no specs yet.

## Impact

- `plugin/plugin.py` and `plugin/config.json` are rewritten. `pactl` becomes a declared dependency.
- `chrome-extension/` and `firefox-extension/` are deleted.
- `README.md` is rewritten for the new install and configuration.
- After upgrading, enable the plugin in SafeEyes settings. It is currently disabled. Unload any installed browser extensions.
- Slack huddles are covered from the start, so the planned Slack extension is no longer needed.
