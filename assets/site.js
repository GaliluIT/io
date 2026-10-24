(function () {
  var root = document.documentElement;
  function store(key, value) {
    try { localStorage.setItem(key, value); } catch (e) {}
  }
  function media(query) {
    return window.matchMedia ? window.matchMedia(query) : { matches: false };
  }

  // Display: light, dark or high contrast. Until the visitor picks one, the site
  // follows their device settings. The choice is set in the page head before it paints.
  var themeButtons = document.querySelectorAll("[data-set-theme]");
  function currentTheme() {
    var chosen = root.getAttribute("data-theme");
    if (chosen) return chosen;
    if (media("(prefers-contrast: more)").matches) return "contrast";
    return media("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }
  function markTheme() {
    var theme = currentTheme();
    themeButtons.forEach(function (b) {
      b.setAttribute("aria-pressed", String(b.getAttribute("data-set-theme") === theme));
    });
  }
  themeButtons.forEach(function (b) {
    b.addEventListener("click", function () {
      var theme = b.getAttribute("data-set-theme");
      root.setAttribute("data-theme", theme);
      store("site-theme", theme);
      markTheme();
    });
  });
  ["(prefers-color-scheme: dark)", "(prefers-contrast: more)"].forEach(function (q) {
    var m = media(q);
    if (m.addEventListener) m.addEventListener("change", markTheme);
  });
  markTheme();

  // Language: English / Español. Image descriptions follow the language too.
  var langButtons = document.querySelectorAll("[data-set-lang]");
  function showLang(lang) {
    root.setAttribute("data-lang", lang);
    langButtons.forEach(function (b) {
      b.setAttribute("aria-pressed", String(b.getAttribute("data-set-lang") === lang));
    });
    document.querySelectorAll("img[data-alt-" + lang + "]").forEach(function (img) {
      img.setAttribute("alt", img.getAttribute("data-alt-" + lang));
    });
  }
  showLang(root.getAttribute("data-lang") || "en");
  langButtons.forEach(function (b) {
    b.addEventListener("click", function () {
      var lang = b.getAttribute("data-set-lang");
      showLang(lang);
      store("site-lang", lang);
    });
  });

  // Viewer: on a project page, pictures and videos open large, one at a time,
  // with arrows to move between them and an X to go back to the page.
  // Keyboard: left and right arrows to move, Esc to close. On touch screens, swipe.
  (function () {
    if (!window.HTMLDialogElement) return;
    var items = [];
    document.querySelectorAll("main figure").forEach(function (fig) {
      var link = fig.querySelector("a[data-viewer]");
      var vid = link ? null : fig.querySelector("video");
      if (!link && !vid) return;
      var cap = fig.querySelector("figcaption");
      var item = { caption: cap ? cap.innerHTML : "" };
      if (link) {
        var img = link.querySelector("img");
        item.type = "image";
        item.src = link.getAttribute("href");
        item.alt = img ? img.getAttribute("alt") || "" : "";
        item.trigger = link;
      } else {
        item.type = "video";
        item.src = vid.getAttribute("src");
        item.poster = vid.getAttribute("poster") || "";
        item.label = vid.getAttribute("aria-label") || "";
        item.inline = vid;
        var open = document.createElement("button");
        open.type = "button";
        open.className = "viewer-expand";
        open.textContent = "View larger";
        open.setAttribute("aria-label", "View larger: " + item.label);
        (cap || fig).appendChild(open);
        item.trigger = open;
      }
      items.push(item);
    });
    if (!items.length) return;

    var icon = {
      close: '<svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" fill="none"/></svg>',
      prev: '<svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true"><path d="M15 5l-7 7 7 7" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" fill="none"/></svg>',
      next: '<svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true"><path d="M9 5l7 7-7 7" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" fill="none"/></svg>'
    };
    var box = document.createElement("dialog");
    box.className = "lb";
    box.setAttribute("aria-label", "Pictures and videos");
    box.innerHTML =
      '<div class="lb-bar"><p class="lb-count" aria-live="polite"></p>' +
      '<button type="button" class="lb-close" aria-label="Close and go back to the page">' + icon.close + '</button></div>' +
      '<div class="lb-stage">' +
      '<button type="button" class="lb-prev" aria-label="Previous">' + icon.prev + '</button>' +
      '<figure class="lb-figure"><div class="lb-media"></div><figcaption class="lb-caption"></figcaption></figure>' +
      '<button type="button" class="lb-next" aria-label="Next">' + icon.next + '</button></div>';
    document.body.appendChild(box);
    var mediaBox = box.querySelector(".lb-media");
    var caption = box.querySelector(".lb-caption");
    var count = box.querySelector(".lb-count");
    var prevBtn = box.querySelector(".lb-prev");
    var nextBtn = box.querySelector(".lb-next");
    var current = 0, opener = null;
    if (items.length < 2) { prevBtn.hidden = true; nextBtn.hidden = true; }

    function stopVideo() {
      var v = mediaBox.querySelector("video");
      if (v) v.pause();
    }
    function show(i) {
      stopVideo();
      current = (i + items.length) % items.length;
      var it = items[current];
      mediaBox.innerHTML = "";
      var el;
      if (it.type === "image") {
        el = document.createElement("img");
        el.src = it.src;
        el.alt = it.alt;
      } else {
        el = document.createElement("video");
        el.src = it.src;
        if (it.poster) el.poster = it.poster;
        el.controls = true;
        el.setAttribute("playsinline", "");
        el.setAttribute("preload", "metadata");
        el.setAttribute("aria-label", it.label);
      }
      mediaBox.appendChild(el);
      caption.innerHTML = it.caption;
      caption.querySelectorAll("[id]").forEach(function (n) { n.removeAttribute("id"); });
      caption.querySelectorAll(".viewer-expand").forEach(function (n) { n.remove(); });
      caption.hidden = !caption.textContent.trim();
      count.textContent = items.length > 1 ? (current + 1) + " of " + items.length : "";
      [current + 1, current - 1].forEach(function (k) {
        var n = items[(k + items.length) % items.length];
        if (n.type === "image") { var pre = new Image(); pre.src = n.src; }
      });
    }
    function openAt(i, from) {
      items.forEach(function (it) { if (it.inline) it.inline.pause(); });
      opener = from || null;
      show(i);
      root.classList.add("lb-open");
      box.showModal();
      box.querySelector(".lb-close").focus();
    }
    function closeBox() {
      if (box.open) box.close();
    }
    box.addEventListener("close", function () {
      stopVideo();
      mediaBox.innerHTML = "";
      root.classList.remove("lb-open");
      if (opener) opener.focus();
    });

    items.forEach(function (it, i) {
      it.trigger.addEventListener("click", function (e) {
        if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button > 0) return;
        e.preventDefault();
        openAt(i, it.trigger);
      });
    });
    prevBtn.addEventListener("click", function () { show(current - 1); });
    nextBtn.addEventListener("click", function () { show(current + 1); });
    box.querySelector(".lb-close").addEventListener("click", closeBox);
    box.addEventListener("click", function (e) {
      if (e.target === box || e.target.classList.contains("lb-stage") || e.target === mediaBox) closeBox();
    });
    box.addEventListener("keydown", function (e) {
      if (e.target.tagName === "VIDEO") return;
      if (e.key === "ArrowRight") { e.preventDefault(); show(current + 1); }
      else if (e.key === "ArrowLeft") { e.preventDefault(); show(current - 1); }
    });
    var startX = null, startY = 0;
    mediaBox.addEventListener("pointerdown", function (e) {
      if (e.target.tagName === "VIDEO") { startX = null; return; }
      startX = e.clientX; startY = e.clientY;
    });
    mediaBox.addEventListener("pointerup", function (e) {
      if (startX === null) return;
      var dx = e.clientX - startX, dy = e.clientY - startY;
      startX = null;
      if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy)) show(current + (dx < 0 ? 1 : -1));
    });
  })();

  // The 3D object turns slowly, unless the visitor prefers reduced motion.
  // A button stops and restarts it.
  var viewer = document.querySelector(".specimen model-viewer");
  if (!viewer) return;
  var rotateButton = document.querySelector("[data-rotate-toggle]");
  if (!media("(prefers-reduced-motion: reduce)").matches) {
    viewer.setAttribute("auto-rotate", "");
    if (rotateButton) {
      rotateButton.hidden = false;
      rotateButton.addEventListener("click", function () {
        if (viewer.hasAttribute("auto-rotate")) {
          viewer.removeAttribute("auto-rotate");
          rotateButton.textContent = "Start turning";
        } else {
          viewer.setAttribute("auto-rotate", "");
          rotateButton.textContent = "Stop turning";
        }
      });
    }
  }

  // The model's color follows the display: graphite, like the printed piece,
  // on light backgrounds, and pale on dark ones, so it always stands out.
  function paintModel() {
    if (!viewer.model) return;
    var dark = currentTheme() === "dark";
    viewer.model.materials.forEach(function (m) {
      var pbr = m.pbrMetallicRoughness;
      pbr.setBaseColorFactor(dark ? [0.9, 0.9, 0.88, 1] : [0.2, 0.2, 0.21, 1]);
      pbr.setMetallicFactor(dark ? 0 : 0.35);
      pbr.setRoughnessFactor(dark ? 0.75 : 0.45);
    });
  }
  viewer.addEventListener("load", paintModel);
  if (viewer.loaded) paintModel();
  themeButtons.forEach(function (b) { b.addEventListener("click", paintModel); });
  var darkQuery = media("(prefers-color-scheme: dark)");
  if (darkQuery.addEventListener) darkQuery.addEventListener("change", paintModel);

  // Optional sound: set fono.sound in content/site.yml. A click (not a drag) plays it.
  var soundSrc = viewer.getAttribute("data-sound");
  if (!soundSrc) return;
  var audio = new Audio(soundSrc);
  var button = document.querySelector("[data-play]");
  var startX = 0, startY = 0;

  function toggle() {
    if (audio.paused) {
      audio.currentTime = 0;
      audio.play().catch(function () {});
    } else {
      audio.pause();
    }
  }
  audio.addEventListener("play", function () { if (button) button.textContent = "Stop sound"; });
  audio.addEventListener("pause", function () { if (button) button.textContent = "Play its sound"; });
  audio.addEventListener("ended", function () { if (button) button.textContent = "Play its sound"; });

  viewer.style.cursor = "pointer";
  viewer.addEventListener("pointerdown", function (e) { startX = e.clientX; startY = e.clientY; });
  viewer.addEventListener("pointerup", function (e) {
    if (Math.abs(e.clientX - startX) + Math.abs(e.clientY - startY) < 6) toggle();
  });
  if (button) button.addEventListener("click", toggle);
})();
