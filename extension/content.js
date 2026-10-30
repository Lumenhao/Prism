// 划词浮层：只跟本机 Prism 说话，页面内容不会离开这台机器。

const HOST_ID = "prism-clip-host";
const MAX_WORD = 120;

function isEnglishish(text) {
  const letters = text.match(/[A-Za-z]/g) || [];
  if (!letters.length) return false;
  return letters.length / text.replace(/\s/g, "").length > 0.5;
}

function sentenceAround(range) {
  const node = range.startContainer;
  const block = node && (node.parentElement || node);
  const holder = block && block.closest ? block.closest("p,li,td,h1,h2,h3,h4,blockquote,dd,figcaption,div") : block;
  const full = holder ? holder.innerText || "" : "";
  if (!full) return "";
  const probe = range.toString().slice(0, 24);
  const parts = full.split(/(?<=[.!?。！？])\s+/);
  const hit = parts.find((part) => probe && part.includes(probe));
  return (hit || full).replace(/\s+/g, " ").trim().slice(0, 600);
}

function card() {
  let host = document.getElementById(HOST_ID);
  if (host) return { host, root: host.shadowRoot.querySelector(".root"), shadow: host.shadowRoot };
  host = document.createElement("div");
  host.id = HOST_ID;
  host.style.cssText = "all: initial; position: fixed; z-index: 2147483647; top: 0; left: 0;";
  document.documentElement.appendChild(host);
  const shadow = host.attachShadow({ mode: "open" });
  const style = document.createElement("style");
  style.textContent = `
    :host { all: initial; }
    .root {
      font: 14px/1.6 -apple-system, "Segoe UI", "Noto Sans SC", system-ui, sans-serif;
      color: #22262d; background: #fdfbf7; border: 1px solid #ddd6c8; border-radius: 12px;
      box-shadow: 0 18px 44px rgba(20, 22, 28, .22); width: 320px; padding: 12px 14px 10px;
    }
    .top { display: flex; align-items: baseline; gap: 8px; }
    .w { font-size: 19px; font-weight: 600; letter-spacing: .01em; }
    .p { color: #7a6a55; font-size: 12.5px; }
    .x { margin-left: auto; border: 0; background: transparent; color: #9aa0ac; cursor: pointer; font-size: 16px; line-height: 1; padding: 2px 4px; }
    .t { margin: 6px 0 0; white-space: pre-wrap; max-height: 168px; overflow: auto; }
    .t .pos { color: #9a7430; }
    .m { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; font-size: 11.5px; color: #6b7280; }
    .m span { border: 1px solid #e6e0d4; border-radius: 999px; padding: 1px 7px; background: #f5f2ec; }
    .act { display: flex; gap: 8px; margin-top: 10px; }
    button.b { font: inherit; font-size: 13px; border-radius: 8px; padding: 5px 11px; cursor: pointer; border: 1px solid #ddd6c8; background: #fff; color: #22262d; }
    button.b:hover { border-color: #b85c4a; color: #b85c4a; }
    button.b.save { background: #b85c4a; border-color: #b85c4a; color: #fdfbf7; font-weight: 600; }
    button.b.save:hover { filter: brightness(.94); color: #fdfbf7; }
    .hint { margin-top: 8px; font-size: 12px; color: #b85c4a; }
    .hint.ok { color: #43796b; }
    .off { display: flex; flex-direction: column; gap: 6px; }
    .off h { font-size: 15px; font-weight: 600; }
  `;
  const root = document.createElement("div");
  root.className = "root";
  shadow.append(style, root);
  return { host, root, shadow };
}

function hide() {
  const host = document.getElementById(HOST_ID);
  if (host) host.remove();
}

function esc(value) {
  return String(value).replace(/[&<>"]/g, (ch) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[ch]));
}

function renderTranslation(entry) {
  const lines = (entry.translation || entry.definition || "").split("\n").filter(Boolean).slice(0, 6);
  if (!lines.length) return `<div class="t">词典里有这个词，但没有中文释义。</div>`;
  return `<div class="t">${lines.map((line) => {
    const match = line.match(/^(\[[^\]]+\]|[a-z]\.\s)/);
    return match ? `<div><span class="pos">${esc(match[1])}</span>${esc(line.slice(match[0].length))}</div>` : `<div>${esc(line)}</div>`;
  }).join("")}</div>`;
}

function place(rect) {
  const { host } = card();
  const width = 320;
  const height = host.shadowRoot.querySelector(".root").offsetHeight || 190;
  const left = Math.max(8, Math.min(rect.left + rect.width / 2 - width / 2, innerWidth - width - 8));
  let top = rect.bottom + 8;
  if (top + height > innerHeight - 8) top = Math.max(8, rect.top - height - 8);
  host.style.top = `${Math.round(top)}px`;
  host.style.left = `${Math.round(left)}px`;
}

function show(entry, query, rect, state) {
  const { root } = card();
  const tags = (entry && entry.tags ? entry.tags : []).slice(0, 4);
  const forms = (entry && entry.exchange ? entry.exchange : []).slice(0, 4);
  root.innerHTML = `
    <div class="top">
      <div class="w">${esc(entry ? entry.word : query)}</div>
      ${entry && entry.phonetic ? `<div class="p">/${esc(entry.phonetic)}/</div>` : ""}
      <button class="x" title="关闭 (Esc)">×</button>
    </div>
    ${entry
      ? renderTranslation(entry)
      : `<div class="off"><h>本地词典里没有「${esc(query.slice(0, 40))}」</h><div style="color:#6b7280">短语或专业词可能不在 ECDICT 里；仍然可以存进收件箱，自己补释义。</div></div>`}
    ${tags.length || forms.length
      ? `<div class="m">${tags.map((tag) => `<span>${esc(tag)}</span>`).join("")}${forms.map((form) => `<span>${esc(form)}</span>`).join("")}</div>`
      : ""}
    <div class="act">
      <button class="b save" data-act="save">存到 Anki</button>
      <button class="b" data-act="copy">复制释义</button>
    </div>
    ${state ? `<div class="hint ${state.ok ? "ok" : ""}">${esc(state.text)}</div>` : ""}
  `;
  place(rect);
  root.querySelector(".x").addEventListener("click", hide);
  root.querySelector('[data-act="save"]').addEventListener("click", () => save(query, entry, rect));
  root.querySelector('[data-act="copy"]').addEventListener("click", async () => {
    const text = `${query}${entry && entry.phonetic ? ` /${entry.phonetic}/` : ""} — ${entry ? entry.translation || entry.definition : ""}`;
    await navigator.clipboard.writeText(text).catch(() => {});
    show(entry, query, rect, { ok: true, text: "已复制" });
  });
}

function save(query, entry, rect) {
  const range = window.getSelection().getRangeAt ? (window.getSelection().rangeCount ? window.getSelection().getRangeAt(0) : null) : null;
  const context = range ? sentenceAround(range) : "";
  chrome.runtime.sendMessage(
    {
      type: "clip",
      payload: {
        word: query,
        context,
        url: location.href,
        title: document.title || location.hostname,
        translation: entry ? entry.translation || entry.definition : "",
        phonetic: entry ? entry.phonetic : "",
      },
    },
    (response) => {
      if (response && response.ok && response.stored) {
        show(entry, query, rect, { ok: true, text: "已存入 Prism 收件箱" });
      } else if (response && response.ok && response.queued) {
        show(entry, query, rect, { ok: false, text: `Prism 没开，已排队 ${response.queued} 条，启动后自动补交` });
      } else {
        show(entry, query, rect, { ok: false, text: `保存失败：${(response && response.reason) || "未知错误"}` });
      }
    }
  );
}

let last = "";

async function onSelection() {
  const stored = await chrome.storage.local.get("enabled");
  if (stored.enabled === false) return;
  const selection = window.getSelection();
  const text = (selection ? selection.toString() : "").replace(/\s+/g, " ").trim();
  if (!text || text.length > MAX_WORD || !isEnglishish(text) || text === last) return;
  last = text;
  const rect = selection.rangeCount ? selection.getRangeAt(0).getBoundingClientRect() : null;
  if (!rect || (!rect.width && !rect.height)) return;
  chrome.runtime.sendMessage({ type: "lookup", text }, (response) => {
    if (!response || !response.ok) {
      show(null, text, rect, { ok: false, text: "Prism 没开：先在 E 盘双击 Prism.bat，再划词" });
      return;
    }
    const data = response.data || {};
    show(data.entry || null, text, rect, data.installed ? null : { ok: false, text: "本机词典还没装：Prism → Vocab → 安装本地词典" });
  });
}

document.addEventListener("mouseup", () => setTimeout(onSelection, 30));
document.addEventListener("keyup", (event) => {
  if (event.key === "Escape") hide();
  else if (event.key.startsWith("Arrow")) setTimeout(onSelection, 30);
});
document.addEventListener("mousedown", (event) => {
  const host = document.getElementById(HOST_ID);
  if (host && !host.contains(event.target) && event.target !== host) hide();
}, true);
window.addEventListener("scroll", () => hide(), { passive: true });
window.addEventListener("resize", hide);
if (location.origin === "http://127.0.0.1:7317") hide();
