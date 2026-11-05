# Tasks

## 1. Remove the old presence pipeline

- [x] 1.1 Delete `chrome-extension/` and `firefox-extension/`, and verify that `git ls-files` lists no extension files
- [x] 1.2 Move `plugin/.gitignore` to the repository root, so that `tests/` is covered too, and verify that `git status --ignored` lists `plugin/__pycache__/` as ignored

## 2. Meeting detection

- [x] 2.1 Add `tests/fixtures/` with `pactl -f json list source-outputs` output for these cases: idle (filter only), Firefox call, Chrome call with two streams, Slack huddle, `handy` only, and an empty list. Base them on a real capture from this machine, and verify that each file parses as JSON
- [x] 2.2 Write failing tests in `tests/test_plugin.py` for parsing capturing binaries from the fixtures, and run `pytest` to see them fail
- [x] 2.3 Implement the parsing function in `plugin/plugin.py`, and verify that the parsing tests pass
- [x] 2.4 Write failing tests for the meeting decision: a listed app capturing, an unlisted app only, the 1-second drop, 30 seconds after the last capture, and no capture ever seen. Then implement the decision function and verify that the tests pass
- [x] 2.5 Write a failing test where `pactl` fails or prints invalid JSON, and expect no capture plus a log line. Implement the error handling and verify that the test passes
- [x] 2.6 Implement the polling thread and the `meeting_apps` setting, which `init` must start only once. Verify this with a test that calls `init` twice and checks that one thread runs

## 3. Break postponement

- [x] 3.1 Write failing tests for the hooks: during a meeting, `on_start_break` sets `context.postponed` and returns `False`. Outside a meeting, it leaves `context.postponed` unchanged. The plugin does not implement `on_pre_break`. Implement the hooks and verify that the tests pass
- [x] 3.2 Rewrite `plugin/config.json`: replace the ten presence settings with a `meeting_apps` TEXT setting whose default is `firefox chrome chromium slack`, declare `pactl` under `shell_commands`, remove `break_override_allowed`, and rename the plugin to "Meeting Do Not Disturb" (later renamed in 5.4). Verify with a test that loads the file and checks the setting ids and the default

## 4. Documentation

- [x] 4.1 Rewrite `README.md` to cover how detection works, installation as a symlink, the `meeting_apps` setting, and the migration steps from design.md. Verify that the README mentions extensions only in the upgrade steps, and no longer mentions port 6776 or presence states
- [x] 4.2 Write `docs/manual-test.md` with the step-by-step test and the results table from 2026-11-03, plus a check that a break during a call is postponed

## 5. Integration check on this machine

- [x] 5.1 Restart SafeEyes, enable the plugin, and verify in the SafeEyes log that the plugin loaded and that no server listens on port 6776 (`ss -ltn | grep 6776` prints nothing)
- [x] 5.2 Join a solo Meet call, run `safeeyes --take-break`, and verify that the break is postponed during the call and shown within the postpone duration plus 30 seconds after leaving it
- [x] 5.3 Enable strict mode and repeat 5.2
- [x] 5.4 Rename the plugin id to `meeting-postpone`, the display name to "Postpone During Meetings", and the repository to `safeeyes-plugin-meeting-postpone`. Verify that SafeEyes loads `meeting-postpone.plugin` with the plugin enabled, and that `git remote -v` points to the renamed repository

## Workflow follow-up

- Archive the change once the integration check passes.
- Push the branch to GitHub. The local branch was already 7 commits ahead before this change.
