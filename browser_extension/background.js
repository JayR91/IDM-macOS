const SERVER = "http://127.0.0.1:27182";

async function sendToApp(url, filename) {
  try {
    const resp = await fetch(`${SERVER}/add`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, filename }),
    });
    return resp.ok;
  } catch (e) {
    console.warn("IDM Clone: could not reach local app (is it running?)", e);
    return false;
  }
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
    id: "send-to-idmclone",
    title: "Download with IDM Clone",
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
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg && msg.type === "idm_download") {
    sendToApp(msg.url).then((ok) => sendResponse({ ok }));
    return true;
  }
});
