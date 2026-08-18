const cb = document.getElementById("intercept");
const statusEl = document.getElementById("status");
const SERVER = "http://127.0.0.1:27182";

chrome.storage.local.get(["intercept"], (res) => {
  cb.checked = !!res.intercept;
});

cb.addEventListener("change", () => {
  chrome.storage.local.set({ intercept: cb.checked });
});

document.getElementById("sendTab").addEventListener("click", async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  statusEl.textContent = "Sending…";
  try {
    const resp = await fetch(`${SERVER}/add`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: tab.url }),
    });
    statusEl.textContent = resp.ok ? "Sent to IDM." : "Failed — is the app running?";
  } catch (e) {
    statusEl.textContent = "Could not reach the app. Is it running?";
  }
});
