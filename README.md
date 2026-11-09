# SafeEyes Postpone During Meetings

A [SafeEyes](https://github.com/slgobinath/SafeEyes) plugin that postpones breaks while you are in a call. It works with strict mode, so you can make breaks unskippable without a break screen covering a meeting.

## How it works

Every 5 seconds the plugin asks PipeWire which applications are capturing the microphone (`pactl -f json list source-outputs`). A meeting is running while an application on the meeting-app list holds the microphone, and for 30 seconds after it releases it.

When a break is due during a meeting, the plugin postpones it by the SafeEyes postpone duration. SafeEyes retries the break after that time, and the plugin postpones it again until the meeting ends.

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

## Configuration

**Meeting apps** is a space-separated list of process names. The default is `firefox chrome chromium slack`.

Set **Meeting apps** to `*` to postpone breaks during microphone capture by any application, including Firefox Nightly and apps without a process name. This mode queries both `source-outputs` and `sources`, ignores corked streams and speaker-monitor sources, and still counts muted but uncorked microphone streams. It uses the same polling interval and 30-second grace period as the app list.

Wildcard mode also postpones breaks during dictation and microphone recording outside meetings. If an app closes or corks its stream while muted, microphone metadata cannot distinguish that call from an ended call after the grace period.

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

## Attributions

<a href="https://www.flaticon.com/free-icons/do-not-disturb" title="do not disturb icons">Do not disturb icons created by Moon.de - Flaticon</a>
