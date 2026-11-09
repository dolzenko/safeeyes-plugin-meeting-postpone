# SafeEyes Postpone During Meetings

A [SafeEyes](https://github.com/slgobinath/SafeEyes) plugin that postpones breaks while you are in a call. It works with strict mode, so you can make breaks unskippable without a break screen covering a meeting.

## How it works

Every 5 seconds the plugin asks PipeWire which applications are capturing the microphone (`pactl -f json list source-outputs`). A meeting is running while an application on the meeting-app list holds the microphone, and for 30 seconds after it releases it.

When a break is due during a meeting, the plugin postpones it before the pre-break warning by the SafeEyes postpone duration. SafeEyes retries the same break after that time, and the plugin postpones it again until the meeting ends. It also checks again before the break screen, in case a call starts during the warning countdown.

This covers any call in a browser or desktop app that uses the microphone, for example Google Meet, Microsoft Teams and Slack huddles. Muting in the app or with the keyboard still counts as being in the call. A tab or app left open after the call does not.

## Requirements

- Linux with PipeWire and `pipewire-pulse`, or PulseAudio, so that `pactl` is installed
- SafeEyes. Tested with 3.5.0.

## Installation

1. Link the `plugin/` directory into the SafeEyes plugins directory. The link name is the plugin id, and SafeEyes stores the plugin's settings under it:

   ```bash
   ln -s "$PWD/plugin" ~/.config/safeeyes/plugins/meeting-postpone
   ```

2. Restart SafeEyes.
3. In SafeEyes settings, enable **Postpone During Meetings**.
4. In `~/.config/safeeyes/safeeyes.json`, move its `meeting-postpone` entry before `notification` and `audiblealert` in the `plugins` list. SafeEyes calls plugins in this order; this lets the plugin suppress the warning and sound as well as the break screen. Restart SafeEyes after editing the file.

## Configuration

**Meeting apps** is a space-separated list of process names. The default is `firefox chrome chromium slack`.

To find the name of another app, start a call in it and run:

```bash
pactl -f json list source-outputs | grep application.process.binary
```

Do not add apps that use the microphone outside meetings, such as dictation tools. Their breaks would be postponed too.

## Upgrading from the browser-extension version

1. Quit SafeEyes and pull the new version.
2. Remove the `teams-do-not-disturb` link from `~/.config/safeeyes/plugins/`, and create the `meeting-postpone` link as in [Installation](#installation). The plugin id has changed, so SafeEyes treats it as a new plugin.
3. Start SafeEyes, and enable the plugin in its settings. The old version could run its server while it was disabled. The new one does nothing until you enable it.
4. Remove the Teams and Google Meet presence extensions from your browsers.
5. Run the [manual test](docs/manual-test.md) before you enable strict mode.

## Development

```bash
pytest -q
```

The optional `tests/test_safeeyes_core.py` tests use an installed SafeEyes to check warning suppression and preservation of short and long breaks. They replace timers, notifications and break windows with test doubles, and do not open windows or play audio. Without SafeEyes installed, these integration tests are skipped.

## Attributions

<a href="https://www.flaticon.com/free-icons/do-not-disturb" title="do not disturb icons">Do not disturb icons created by Moon.de - Flaticon</a>
