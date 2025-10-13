# SafeEyes Do Not Disturb - Multi-Platform

Automatically skip SafeEyes breaks when you're in a meeting or have specific presence status on Microsoft Teams or Google Meet.

## Features

- **Multi-platform support**: Works with both Microsoft Teams and Google Meet
- **Granular control**: Configure which presence states should skip breaks
- **Browser extensions**: Chrome extension for Teams, Firefox extension for Google Meet
- **SafeEyes plugin**: Receives presence updates via local webhook

## Architecture

```
┌─────────────────────┐         ┌─────────────────────┐
│ Chrome Extension    │         │ Firefox Extension   │
│ (Teams)             │         │ (Google Meet)       │
└──────────┬──────────┘         └──────────┬──────────┘
           │                               │
           │    POST http://localhost:6776 │
           │         {status: "..."}       │
           └───────────────┬───────────────┘
                           │
                  ┌────────▼────────┐
                  │  SafeEyes       │
                  │  Plugin         │
                  │  (HTTP Server)  │
                  └─────────────────┘
```

## Installation

### 1. Install Browser Extensions

#### For Microsoft Teams (Chrome)
1. Open Chrome
2. Navigate to `chrome://extensions`
3. Enable "Developer mode"
4. Click "Load unpacked"
5. Select the `chrome-extension/` directory

#### For Google Meet (Firefox)
1. Open Firefox
2. Navigate to `about:debugging#/runtime/this-firefox`
3. Click "Load Temporary Add-on"
4. Select `firefox-extension/manifest.json`

### 2. Install SafeEyes Plugin

Copy the `plugin/` directory to your SafeEyes plugins directory:

```bash
cp -r plugin ~/.config/safeeyes/plugins/do-not-disturb
```

Then enable and configure the plugin in SafeEyes settings.

## Configuration

The plugin provides individual toggles for each presence state:

### Google Meet States
- **in-a-meeting**: Active call in progress (default: enabled)
- **available**: Not in a call (default: disabled)

### Microsoft Teams States
- **on the phone**: Active call (default: enabled)
- **presenting**: Screen sharing (default: enabled)
- **online**: Available (default: disabled)
- **busy**: Busy status (default: disabled)
- **do not disturb**: DND mode (default: disabled)
- **be right back**: BRB status (default: disabled)
- **away**: Away status (default: disabled)
- **offline**: Offline (default: disabled)

## How It Works

1. Browser extensions monitor presence status on their respective platforms
2. When status changes, they POST to `http://localhost:6776` with format:
   ```json
   {
     "status": "in-a-meeting"
   }
   ```
3. SafeEyes plugin receives the update and checks configuration
4. If the status is configured to skip breaks, upcoming breaks are cancelled

## Development Notes

### Status Normalization

The plugin automatically normalizes status strings:
- Hyphens and spaces are converted to underscores
- Example: `"in-a-meeting"` → `presence_in_a_meeting`
- Example: `"on the phone"` → `presence_on_the_phone`

### Port Configuration

The webhook server runs on port `6776` by default. This is configured in `plugin/plugin.py` line 96.

## Troubleshooting

- **Plugin not receiving updates**: Check that the browser extension is loaded and active
- **Breaks not being skipped**: Verify the presence state is enabled in SafeEyes plugin settings
- **Port conflicts**: Ensure port 6776 is not in use by another application

## Attributions

<a href="https://www.flaticon.com/free-icons/do-not-disturb" title="do not disturb icons">Do not disturb icons created by Moon.de - Flaticon</a>
