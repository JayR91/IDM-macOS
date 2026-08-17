(function () {
  const BTN_CLASS = "idm-clone-overlay-btn";
  const IDLE_LABEL = "⬇ IDM";
  const ATTACHED_ATTR = "data-idm-attached";

  // Resolve the URL for the specific post a <video> belongs to, not just
  // "the current page" -- X/Twitter (and similar feeds) can show many
  // videos on one page, each from a different post. Walk up to the
  // enclosing <article> (the standard wrapper for one feed item) and use
  // its permalink (the /status/... link). Falls back to the page URL for
  // single-video pages (YouTube, Vimeo, a single Reddit/X post, ...).
  function findPostUrl(video) {
    // Element.closest() walks all the way to the document root with no
    // depth limit -- needed here since X nests a tweet's <video> as much
    // as 20+ DOM levels below its <article> wrapper.
    const article = video.closest("article");
    if (article) {
      const link =
        article.querySelector('a[href*="/status/"]') ||
        article.querySelector("a[href] time")?.closest("a");
      if (link && link.href) return link.href;
    }
    return location.href;
  }

  function makeButton(video) {
    const btn = document.createElement("div");
    btn.className = BTN_CLASS;
    btn.textContent = IDLE_LABEL;
    Object.assign(btn.style, {
      position: "absolute",
      top: "8px",
      left: "8px",
      zIndex: 2147483647,
      background: "rgba(20,20,20,0.85)",
      color: "#fff",
      fontFamily: "Arial, Helvetica, sans-serif",
      fontWeight: "bold",
      fontSize: "12px",
      padding: "5px 10px",
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

    // The ONLY thing that ever triggers a send is a direct click on this
    // button. Attaching the overlay (including as videos scroll in/out of
    // view) never downloads anything by itself.
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      e.stopImmediatePropagation();
      const url = findPostUrl(video);
      btn.textContent = "Sending…";
      chrome.runtime.sendMessage({ type: "idm_download", url }, (resp) => {
        btn.textContent = resp && resp.ok ? "✓ Sent to IDM" : "✗ App not running";
        setTimeout(() => (btn.textContent = IDLE_LABEL), 2200);
      });
    });
    ["mousedown", "mouseup"].forEach((evt) =>
      btn.addEventListener(evt, (e) => e.stopPropagation())
    );
    return btn;
  }

  function attach(video) {
    if (video.hasAttribute(ATTACHED_ATTR)) return;
    const container = video.parentElement;
    if (!container) return;
    video.setAttribute(ATTACHED_ATTR, "1");
    if (getComputedStyle(container).position === "static") {
      container.style.position = "relative";
    }
    container.appendChild(makeButton(video));
    // If the video is later removed from the page (e.g. scrolled out and
    // recycled by X's virtualized timeline), the button goes with it since
    // it lives inside the same subtree -- nothing to clean up by hand.
  }

  function scan() {
    document.querySelectorAll(`video:not([${ATTACHED_ATTR}])`).forEach(attach);
  }

  // Debounce bursts of DOM mutations (X's feed churns heavily while
  // scrolling) into at most one scan per animation frame.
  let scheduled = false;
  function scheduleScan() {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(() => {
      scheduled = false;
      scan();
    });
  }

  new MutationObserver(scheduleScan).observe(document.documentElement, {
    childList: true,
    subtree: true,
  });

  scan();
  // Safety-net poll in case a site adds/replaces <video> elements without
  // triggering a childList mutation the observer catches.
  setInterval(scan, 1500);
})();
