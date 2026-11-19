// Open WebUI sets the root class from its System, Light or Dark preference.
(() => {
  const root = document.documentElement;
  function updateIcons() {
    const dark = root.classList.contains("dark");
    document.querySelector('link[rel="apple-touch-icon"]').href =
      dark ? "/static/apple-touch-icon-dark.png" : "/static/apple-touch-icon.png";
    document.querySelector('link[rel="manifest"]').href =
      dark ? "/static/manifest-dark.webmanifest" : "/manifest.json";
  }
  updateIcons();
  new MutationObserver(updateIcons).observe(root, { attributes: true, attributeFilter: ["class"] });
  // Model avatars can redirect to the app mark or to custom artwork. Identify
  // only same-origin app-mark responses; never theme custom profile photos.
  async function identifyModelFallback(img) {
    if (!(img instanceof HTMLImageElement)) return;
    const src = img.currentSrc;
    if (!src.startsWith(location.origin + "/api/v1/models/model/profile/image?")) return;
    if (img.dataset.bbChecked === src) return;
    img.dataset.bbChecked = src;
    img.classList.remove("bb-default-model-icon");
    try {
      const response = await fetch(src, { mode: "same-origin", cache: "force-cache" });
      if (img.currentSrc === src && response.url === location.origin + "/static/favicon.png") {
        img.classList.add("bb-default-model-icon");
      }
    } catch {
      // Cross-origin custom avatars keep their original presentation.
    }
  }
  document.addEventListener("load", event => {
    const img = event.target;
    if (img instanceof HTMLImageElement && img.dataset.bbChecked !== img.currentSrc) {
      img.classList.remove("bb-default-model-icon");
      delete img.dataset.bbChecked;
      identifyModelFallback(img);
    }
  }, true);
  document.querySelectorAll("img").forEach(identifyModelFallback);
  // The hydrated client appends a PNG favicon after the SVG in the initial head.
  function preferVectorIcon() {
    for (const link of document.head.querySelectorAll('link[rel="icon"][href="/static/favicon.png"]')) {
      link.type = "image/svg+xml";
      link.sizes = "any";
      link.href = "/static/favicon.svg";
    }
  }
  preferVectorIcon();
  new MutationObserver(preferVectorIcon).observe(document.head, { childList: true });
})();
