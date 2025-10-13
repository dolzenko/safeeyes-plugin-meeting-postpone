// Global state
let currentInMeeting = null;

function notifyBackgroundScript(inMeeting) {
    console.log('[Google Meet Content] In meeting:', inMeeting);
    browser.runtime.sendMessage({
        type: 'meeting-status',
        inMeeting: inMeeting
    });
}

function detectGoogleMeetPresence() {
    // Simple detection: if page title starts with "Meet – " (en-dash), user is in a meeting
    const title = document.title;
    const inMeeting = title.startsWith('Meet –');

    // Only notify if status changed
    if (inMeeting !== currentInMeeting) {
        console.log('[Google Meet Content] Status changed:', currentInMeeting, '->', inMeeting);
        currentInMeeting = inMeeting;
        notifyBackgroundScript(inMeeting);
    }
}

function startMonitoring() {
    console.log('[Google Meet] Starting presence monitoring');

    // Initial check
    detectGoogleMeetPresence();

    // Monitor title changes using MutationObserver
    const observer = new MutationObserver(detectGoogleMeetPresence);

    const titleElement = document.querySelector('title');
    if (titleElement) {
        observer.observe(titleElement, {
            childList: true,
            characterData: true,
            subtree: true
        });
    }

    // Fallback: check every 5 seconds in case observer misses changes
    setInterval(detectGoogleMeetPresence, 5000);
}

if (window.location.hostname === 'meet.google.com') {
    // Wait for page to load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', startMonitoring);
    } else {
        startMonitoring();
    }
}
