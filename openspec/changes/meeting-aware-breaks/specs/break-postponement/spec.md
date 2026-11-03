# Spec Delta

## Purpose

Keeps SafeEyes breaks, including strict-mode breaks, from covering a meeting, while making sure the user still takes the break once the meeting ends.

## ADDED Requirements

### Requirement: Break during a meeting is postponed
When a break is about to start and a meeting is running, the plugin SHALL postpone the break by the SafeEyes postpone duration instead of showing the break screen.

#### Scenario: Break falls due during a call
- **WHEN** a break is about to start and a meeting is running
- **THEN** no break screen appears, and SafeEyes schedules the same break again after the postpone duration

#### Scenario: Strict mode is on
- **WHEN** strict mode is enabled and a break falls due during a meeting
- **THEN** the break is postponed the same way

#### Scenario: Postpone button disabled
- **WHEN** the user has disabled the Postpone button in SafeEyes
- **THEN** the plugin still postpones the break

### Requirement: Postponed break retries until the meeting ends
The plugin SHALL postpone the break again each time it falls due while a meeting is still running.

#### Scenario: Long meeting
- **WHEN** a postponed break falls due again and the meeting is still running
- **THEN** the break is postponed again

#### Scenario: Meeting has ended
- **WHEN** a postponed break falls due and no meeting is running
- **THEN** the break screen appears as normal

### Requirement: Break outside a meeting is unaffected
The plugin SHALL NOT skip, postpone or delay a break when no meeting is running.

#### Scenario: No meeting
- **WHEN** a break falls due and no meeting is running
- **THEN** the break proceeds exactly as it would without the plugin

#### Scenario: Detection fails
- **WHEN** a break falls due and the plugin cannot read the capture streams
- **THEN** the break proceeds
