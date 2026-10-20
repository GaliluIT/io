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
