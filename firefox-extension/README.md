# Google Meet Presence Detector - Firefox Extension

A Firefox extension that detects presence status from Google Meet and sends updates to a local webhook for SafeEyes integration.

## Supported Platforms

- Google Meet (https://meet.google.com/*)

## How It Works

The extension monitors the presence status on Google Meet by:
1. **Google Meet**: Detects active meetings by monitoring page title changes (title starts with "Meet – " when in a call)
2. Sends status updates when presence changes
3. Sends POST requests to `http://localhost:6776` with status updates

## Webhook Format

```json
{
  "status": "in-a-meeting" | "available"
}
```

### Status Values

- `in-a-meeting`: User is currently in an active Google Meet call
- `available`: User is not in a call or has left the meeting

## Installation

### For Development

1. Open Firefox
2. Navigate to `about:debugging#/runtime/this-firefox`
3. Click "Load Temporary Add-on"
4. Select the `manifest.json` file from this directory

## Architecture

- **Manifest V3**: Future-proof extension format
- **Background Script**: Tracks meeting state across multiple tabs
- **Content Script**: Platform-specific presence detection
- **Local Webhook**: Sends updates to localhost:6776 for SafeEyes plugin integration

## Integration with SafeEyes

This extension works with the SafeEyes "Do Not Disturb" plugin to automatically skip breaks when you're in a Google Meet call. Make sure the SafeEyes plugin is installed and configured to skip breaks when status is "in-a-meeting".
