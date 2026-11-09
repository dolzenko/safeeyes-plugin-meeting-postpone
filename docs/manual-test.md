# Manual test

Run this test after you install or upgrade the plugin, after a SafeEyes upgrade, and before you enable strict mode. It needs about 15 minutes.

## 1. Check detection

You can test alone: start an instant meeting with `meet.google.com/new`, use **Meet now** in Teams, or start a huddle in your own Slack DM.

1. In a terminal, start the watcher:

   ```bash
   watch -n1 "pactl -f json list source-outputs | grep -o '\"application.process.binary\":\"[^\"]*\"'"
   ```

2. Do the steps below in order. After each step, compare the watcher output with the expected result.

| Step | Expected watcher output |
|---|---|
| Join the call | The app's process name appears, for example `firefox`, `chrome` or `slack` |
| Mute in the app | The name stays |
| Mute with the keyboard (`Meta+Volume Mute` on KDE) | The name stays |
| Unmute with the keyboard | The name stays |
| Leave the call, and keep the tab or app open | The name disappears within a few seconds |

If the name disappears while you are still in the call, the plugin will not protect that app. If the name stays after you leave the call, breaks are postponed until you close the tab or app.

## 2. Check postponement

1. Join a call.
2. Wait 10 seconds, so that the plugin's next poll sees the call.
3. Run `safeeyes --take-break`.
4. Make sure that no pre-break notification, warning sound or break screen appears. The plugin must precede `notification` and `audiblealert` in the configuration's `plugins` list. If SafeEyes runs with `--debug`, `~/safeeyes.log` also shows "Postponing the break".
5. Leave the call.
6. Make sure that the break screen appears within the postpone duration plus 30 seconds.

If strict mode is on, repeat these steps.

## Results

On 2026-11-03, with SafeEyes 3.5.0 and PipeWire 1.6.8:

| App | Join | Mute in app | Mute with keyboard | Leave, app still open |
|---|---|---|---|---|
| Google Meet, Firefox | ✅ | ✅ | ✅ | ✅ |
| Google Meet, Chrome | ✅ | ✅ | ✅ | ✅ |
| Microsoft Teams, Chrome | ✅ | ✅ | ✅ | ✅ |
| Slack desktop huddle | ✅ | ✅ | ✅ | ✅ |

Chrome holds two capture streams per call. Slack drops its stream for about 1 second while a huddle starts, and the 30-second grace period covers that drop. Teams in Firefox was not tested.
