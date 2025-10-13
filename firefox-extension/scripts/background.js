// Track active meeting tabs
let meetingTabs = new Set();
let currentStatus = null;

function sendPresenceUpdate(status) {
    if (status === currentStatus) return;

    console.log('[Google Meet Presence] Sending status:', status);
    currentStatus = status;

    fetch('http://localhost:6776', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: status })
    }).catch(err => console.error('[Google Meet Presence] Error:', err));
}

function updatePresenceStatus() {
    const status = meetingTabs.size > 0 ? 'in-a-meeting' : 'available';
    sendPresenceUpdate(status);
}

// Listen for messages from content scripts
browser.runtime.onMessage.addListener((message, sender) => {
    if (message.type === 'meeting-status') {
        const tabId = sender.tab.id;

        if (message.inMeeting) {
            meetingTabs.add(tabId);
        } else {
            meetingTabs.delete(tabId);
        }

        updatePresenceStatus();
    }
});

// Clean up when tabs are closed
browser.tabs.onRemoved.addListener((tabId) => {
    if (meetingTabs.has(tabId)) {
        meetingTabs.delete(tabId);
        updatePresenceStatus();
    }
});

// Clean up when tabs navigate away from Meet
browser.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.url && meetingTabs.has(tabId)) {
        if (!tab.url.startsWith('https://meet.google.com/')) {
            meetingTabs.delete(tabId);
            updatePresenceStatus();
        }
    }
});

console.log('[Google Meet Presence] Background script loaded');
