(function () {
  const BTN_ID = "idm-clone-overlay-btn";
  const IDLE_LABEL = "⬇ IDM";

  function removeButton() {
    const el = document.getElementById(BTN_ID);
    if (el) el.remove();
  }

  function injectButton() {
    if (!location.pathname.startsWith("/watch")) {
      removeButton();
      return;
    }
    const player = document.querySelector(".html5-video-player");
    if (!player || document.getElementById(BTN_ID)) return;

    const btn = document.createElement("div");
    btn.id = BTN_ID;
    btn.textContent = IDLE_LABEL;
    Object.assign(btn.style, {
      position: "absolute",
      top: "10px",
      left: "10px",
      zIndex: 2147483647,
      background: "rgba(20,20,20,0.85)",
      color: "#fff",
      fontFamily: "Arial, Helvetica, sans-serif",
      fontWeight: "bold",
      fontSize: "13px",
      padding: "6px 12px",
      borderRadius: "6px",
      cursor: "pointer",
      userSelect: "none",
      boxShadow: "0 2px 6px rgba(0,0,0,0.4)",
      transition: "background 0.15s",
    });
    btn.addEventListener("mouseenter", () => {
      btn.style.background = "rgba(200,30,30,0.9)";
    });
    btn.addEventListener("mouseleave", () => {
      btn.style.background = "rgba(20,20,20,0.85)";
    });

    btn.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      e.stopImmediatePropagation();
      const url = location.href;
      btn.textContent = "Sending…";
      chrome.runtime.sendMessage({ type: "idm_download", url }, (resp) => {
        btn.textContent = resp && resp.ok ? "✓ Sent to IDM" : "✗ App not running";
        setTimeout(() => (btn.textContent = IDLE_LABEL), 2200);
      });
    });
    // Swallow other mouse events too, so clicks on the button never reach
    // the player underneath (which would toggle play/pause).
    ["mousedown", "mouseup"].forEach((evt) =>
      btn.addEventListener(evt, (e) => e.stopPropagation())
    );

    if (!player.style.position) player.style.position = "relative";
    player.appendChild(btn);
  }

  let lastUrl = location.href;
  function onPossibleNav() {
    if (location.href === lastUrl) return;
    lastUrl = location.href;
    removeButton();
    setTimeout(injectButton, 500);
  }

  document.addEventListener("yt-navigate-finish", onPossibleNav);
  new MutationObserver(onPossibleNav).observe(document.documentElement, {
    childList: true,
    subtree: true,
  });

  injectButton();
  setInterval(injectButton, 1500);
})();
