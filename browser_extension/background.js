const SERVER = "http://127.0.0.1:27182";
const APP_LAUNCH_URL = "vdr://launch";

async function postAdd(url, filename) {
  try {
    const resp = await fetch(`${SERVER}/add`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, filename }),
    });
    return resp.ok;
  } catch (e) {
    return false;
  }
}

async function pingApp() {
  try {
    const resp = await fetch(`${SERVER}/ping`);
    return resp.ok;
  } catch (e) {
    return false;
  }
}

// Chrome extensions can't launch a native app directly -- there's no API
// for it, by design. Custom URL schemes are the standard, OS-level bridge
// apps like Zoom/Slack/VS Code use instead: the app registers one at
// install time, and navigating to it is enough for the OS to start (or
// foreground) that app. The first time, the browser shows a one-time
// "Open in VDR?" confirmation -- that's normal browser/OS behavior
// for any external protocol handler, not something an extension can skip.
function launchApp() {
  return new Promise((resolve) => {
    chrome.tabs.create({ url: APP_LAUNCH_URL, active: false }, (tab) => {
      const tabId = tab && tab.id;
      setTimeout(() => {
        if (tabId) chrome.tabs.remove(tabId, () => void chrome.runtime.lastError);
        resolve();
      }, 2000);
    });
  });
}

async function waitForAppReady(timeoutMs = 10000, intervalMs = 500) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (await pingApp()) return true;
    await new Promise((r) => setTimeout(r, intervalMs));
  }
  return false;
}

async function sendToApp(url, filename) {
  if (await postAdd(url, filename)) return true;

  // Not reachable -- most likely the app just isn't running. Launch it via
  // its registered URL scheme and retry once it responds to /ping, rather
  // than immediately failing the download. (Used by the context menu and
  // download-interception paths below, which run entirely inside this
  // background script with no content script involved.)
  console.warn("VDR: app not reachable, attempting to launch it");
  await launchApp();
  if (!(await waitForAppReady())) return false;
  return postAdd(url, filename);
}

// Intercept native browser downloads (when the toggle is on) and hand them
// to the local app instead, so it can do segmented/resumable downloading.
chrome.downloads.onCreated.addListener((item) => {
  chrome.storage.local.get(["intercept"], async (res) => {
    if (!res.intercept) return;
    const filename = item.filename ? item.filename.split(/[\\/]/).pop() : undefined;
    const ok = await sendToApp(item.url, filename);
    if (ok) {
      chrome.downloads.cancel(item.id, () => chrome.downloads.erase({ id: item.id }));
    }
  });
});

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "send-to-vdr",
    title: "Download with VDR",
    contexts: ["link", "video", "audio"],
  });
});

chrome.contextMenus.onClicked.addListener((info) => {
  const url = info.linkUrl || info.srcUrl;
  if (url) sendToApp(url);
});

// Content scripts (e.g. the YouTube overlay button) can't reliably fetch the
// local app directly -- the page's own CSP can block it. Route through here
// instead, since the background service worker isn't subject to page CSP.
//
// Each message below does exactly one fast, atomic thing (a single fetch,
// or firing off a tab creation) and responds immediately -- the content
// script owns the multi-second launch-and-wait retry loop itself. An MV3
// service worker can be suspended by Chrome between messages, silently
// dropping a response that was still pending ("message channel closed
// before a response was received"); keeping every individual exchange
// short avoids ever being caught mid-suspension.
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (!msg) return;

  if (msg.type === "vdr_try_add") {
    postAdd(msg.url, msg.filename).then((ok) => sendResponse({ ok }));
    return true;
  }

  if (msg.type === "vdr_ping") {
    pingApp().then((ok) => sendResponse({ ok }));
    return true;
  }
});
