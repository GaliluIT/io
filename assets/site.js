(function () {
  // About: English / Español switch. The starting language is set in the page head.
  var root = document.documentElement;
  var buttons = document.querySelectorAll("[data-set-lang]");

  function showLang(lang) {
    root.setAttribute("data-about-lang", lang);
    buttons.forEach(function (b) {
      b.setAttribute("aria-pressed", String(b.getAttribute("data-set-lang") === lang));
    });
  }

  if (buttons.length) {
    showLang(root.getAttribute("data-about-lang") || "en");
    buttons.forEach(function (b) {
      b.addEventListener("click", function () {
        var lang = b.getAttribute("data-set-lang");
        showLang(lang);
        try { localStorage.setItem("about-lang", lang); } catch (e) {}
      });
    });
  }

  // The 3D object: turn slowly unless the visitor prefers reduced motion.
  var viewer = document.querySelector("model-viewer");
  if (!viewer) return;
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (!reduce) viewer.setAttribute("auto-rotate", "");

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
