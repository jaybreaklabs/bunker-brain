// The library itself stays paper. Install artwork follows the device appearance.
const appearance = window.matchMedia("(prefers-color-scheme: dark)");
function updateInstallIcons() {
  const dark = appearance.matches;
  document.querySelector('link[rel="apple-touch-icon"]').href =
    dark ? "/brand/app-icon-dark-180.png" : "/brand/app-icon-180.png";
  document.querySelector('link[rel="manifest"]').href =
    dark ? "/manifest-dark.webmanifest" : "/manifest.webmanifest";
}
updateInstallIcons();
appearance.addEventListener("change", updateInstallIcons);
