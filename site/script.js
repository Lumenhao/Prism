const root = document.documentElement;
const button = document.getElementById("theme");
const meta = document.querySelector('meta[name="theme-color"]');

function paint(theme) {
  root.dataset.theme = theme;
  button.textContent = theme === "dark" ? "浅色" : "深色";
  if (meta) meta.content = theme === "dark" ? "#0f1116" : "#f5f2ec";
}

let saved = new URLSearchParams(location.search).get("theme");
if (saved !== "light" && saved !== "dark") {
  try { saved = localStorage.getItem("prism-site-theme") === "light" ? "light" : "dark"; } catch (_) { saved = "dark"; }
}
paint(saved);

button.addEventListener("click", () => {
  const next = root.dataset.theme === "dark" ? "light" : "dark";
  try { localStorage.setItem("prism-site-theme", next); } catch (_) { /* private mode */ }
  paint(next);
});
