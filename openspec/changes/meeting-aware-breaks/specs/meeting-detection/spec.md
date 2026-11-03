# Spec Delta

## Purpose

Decides whether the user is in a meeting, from which applications are capturing the microphone, so that breaks can wait for the meeting to end.

## ADDED Requirements

### Requirement: Meeting is detected from microphone capture
The plugin SHALL consider a meeting running while at least one application on the meeting-app list is capturing audio from any input source.

#### Scenario: Browser joins a call
- **WHEN** Firefox or Chrome starts capturing the microphone for a Meet or Teams call
- **THEN** a meeting is running

#### Scenario: Slack huddle
- **WHEN** Slack starts capturing the microphone for a huddle
- **THEN** a meeting is running

#### Scenario: Several capture streams from one app
- **WHEN** Chrome holds two capture streams for one call
- **THEN** a meeting is running, the same as with one stream

### Requirement: Only listed applications count
The plugin SHALL ignore capture streams from applications that are not on the meeting-app list. Applications are identified by their process binary name.

#### Scenario: Dictation app holds the mic
- **WHEN** the dictation app `handy` captures the microphone and no listed app does
- **THEN** no meeting is running

#### Scenario: Audio filter holds the mic
- **WHEN** only the always-on noise-canceling filter is capturing
- **THEN** no meeting is running

### Requirement: Meeting-app list is configurable
The plugin SHALL read the meeting-app list from a plugin setting holding space-separated binary names. The default SHALL be `firefox chrome chromium slack`.

#### Scenario: User adds an app
- **WHEN** the user adds `zoom` to the setting and Zoom captures the microphone
- **THEN** a meeting is running

#### Scenario: Default list
- **WHEN** the user has not changed the setting
- **THEN** Firefox, Chrome, Chromium and Slack count as meeting apps

### Requirement: Muting does not end a meeting
The plugin SHALL keep considering a meeting running while the user is muted, whether the mute comes from the meeting app or from the system input source.

#### Scenario: Muted in the app
- **WHEN** the user mutes in Meet, Teams or Slack during a call
- **THEN** a meeting is running

#### Scenario: Muted with the keyboard
- **WHEN** the user mutes the system input source, for example with `Meta+Volume Mute`, during a call
- **THEN** a meeting is running

### Requirement: Meeting ends after a grace period
The plugin SHALL consider a meeting running until no listed application has captured the microphone for 30 seconds.

#### Scenario: Short drop in the capture stream
- **WHEN** a listed app releases the microphone and captures it again 1 second later
- **THEN** the meeting is running throughout

#### Scenario: Call ends with the app still open
- **WHEN** the user leaves the call, keeps the tab or app open, and 30 seconds pass
- **THEN** no meeting is running

### Requirement: Detection failure means no meeting
The plugin SHALL consider no meeting running when it cannot read the capture streams.

#### Scenario: Audio server unavailable
- **WHEN** querying the audio server fails or returns output the plugin cannot parse
- **THEN** no meeting is running, and the plugin logs the failure
