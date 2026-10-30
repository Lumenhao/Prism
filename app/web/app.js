const ICONS = {
  grid: '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
  library: '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2Z"/>',
  mic: '<rect x="9" y="2" width="6" height="12" rx="3"/><path d="M5 10a7 7 0 0 0 14 0"/><path d="M12 19v3"/>',
  pen: '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"/>',
  cards: '<rect x="3" y="5" width="13" height="16" rx="2"/><path d="M8 3h9a2 2 0 0 1 2 2v13"/>',
  sliders: '<path d="M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3"/><path d="M1 14h6M9 8h6M17 16h6"/>',
  search: '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
  play: '<path d="M7 4.5v15l12-7.5Z"/>',
  arrow: '<path d="M5 12h14M13 6l6 6-6 6"/>',
  refresh: '<path d="M20 11a8 8 0 1 0-2.3 5.7"/><path d="M20 4v7h-7"/>',
  upload: '<path d="M12 16V4M7 9l5-5 5 5"/><path d="M4 16v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3"/>',
  speaker: '<path d="M11 5 6 9H3v6h3l5 4Z"/><path d="M15.5 8.5a5 5 0 0 1 0 7"/><path d="M18.5 5.5a9 9 0 0 1 0 13"/>',
  check: '<path d="m4 12 5 5L20 6"/>',
  external: '<path d="M14 4h6v6"/><path d="M20 4 10 14"/><path d="M20 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1h5"/>',
  folder: '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  spark: '<path d="M12 3v4M12 17v4M3 12h4M17 12h4M5.6 5.6l2.8 2.8M15.6 15.6l2.8 2.8M18.4 5.6l-2.8 2.8M8.4 15.6l-2.8 2.8"/>',
  save: '<path d="M5 3h11l3 3v15H5Z"/><path d="M8 3v6h8V3"/><path d="M8 21v-7h8v7"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  x: '<path d="M6 6l12 12M18 6 6 18"/>',
  down: '<path d="m6 9 6 6 6-6"/>',
  book: '<path d="M4 5a2 2 0 0 1 2-2h13v18H6a2 2 0 0 1-2-2Z"/><path d="M4 17h15"/>',
  download: '<path d="M12 4v12M7 11l5 5 5-5"/><path d="M4 20h16"/>',
  zap: '<path d="M13 2 4 14h7l-1 8 9-12h-7Z"/>',
  wave: '<path d="M2 12h3l2-6 3 12 3-9 2 5 2-2h5"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
  moon: '<path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5Z"/>',
  target: '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3"/>',
  layers: '<path d="m12 2 9 5-9 5-9-5Z"/><path d="m3 12 9 5 9-5"/><path d="m3 17 9 5 9-5"/>'
};

function icon(name, cls = "") {
  return `<svg class="${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICONS[name] || ICONS.dot}</svg>`;
}

function mountIcons(root = document) {
  root.querySelectorAll("[data-icon]").forEach((el) => {
    el.innerHTML = icon(el.dataset.icon);
    el.removeAttribute("data-icon");
  });
}

function esc(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function pct(value) { return `${Math.round(value * 100)}%`; }
function clamp(value, min, max) { return Math.max(min, Math.min(max, value)); }

const state = {
  route: "overview",
  overview: null,
  anki: null,
  library: { items: [], q: "", selected: null, detail: null },
  scripts: [],
  script: { name: "sample_talk.md", text: "" },
  report: null,
  speakTab: "listen",
  tts: null,
  links: null,
  writeText: "",
  writeCheck: null,
  phraseFilter: "",
  phrases: [],
  settings: null,
  tools: null,
  paletteIndex: 0
};

async function api(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  if (options.body && !(options.body instanceof FormData)) headers["Content-Type"] = "application/json";
  const response = await fetch(path, { ...options, headers });
  if (!response.ok) {
    let message = response.statusText;
    try {
      const data = await response.json();
      message = data.detail || message;
    } catch (_) { /* ignore */ }
    throw new Error(message);
  }
  return response.json();
}

function toast(message, kind = "") {
  const el = document.getElementById("toast");
  el.textContent = message;
  el.className = `toast ${kind}`;
  el.hidden = false;
  clearTimeout(el._timer);
  el._timer = setTimeout(() => { el.hidden = true; }, 4200);
}

function setRoute(name) { location.hash = `#/${name}`; }

/* --------------------------------------------------------------- theme */

function currentTheme() {
  return document.documentElement.dataset.theme === "light" ? "light" : "dark";
}

function syncThemeIcon() {
  const btn = document.getElementById("theme-toggle");
  if (!btn) return;
  const dark = currentTheme() === "dark";
  btn.innerHTML = icon(dark ? "sun" : "moon");
  btn.title = dark ? "切换到浅色主题 (Ctrl Shift L)" : "切换到深色主题 (Ctrl Shift L)";
}

function applyTheme(theme) {
  const next = theme === "light" ? "light" : "dark";
  document.documentElement.dataset.theme = next;
  try { localStorage.setItem("prism-theme", next); } catch (_) { /* private mode */ }
  if (window.pywebview?.api?.set_theme) {
    window.pywebview.api.set_theme(next).catch(() => {});
  }
  syncThemeIcon();
}

function toggleTheme() { applyTheme(currentTheme() === "dark" ? "light" : "dark"); }

/* --------------------------------------------------------------- shell */

function markNav(route) {
  document.querySelectorAll(".nav-item[data-route]").forEach((el) => {
    el.classList.toggle("active", el.dataset.route === route);
  });
}

function setAnkiChip(status) {
  state.anki = status;
  const dot = document.getElementById("anki-dot");
  const label = document.getElementById("anki-label");
  const badge = document.getElementById("due-badge");
  const ok = Boolean(status && status.connected);
  dot.className = `dot ${ok ? "ok" : "bad"}`;
  label.textContent = ok ? `Anki · ${status.due} due` : "Anki 未连接";
  if (ok && status.due > 0) {
    badge.textContent = status.due > 99 ? "99+" : status.due;
    badge.hidden = false;
  } else {
    badge.hidden = true;
  }
}

async function refreshAnkiChip() {
  try {
    const status = await api("/api/anki/status");
    setAnkiChip(status);
    return status;
  } catch (_) {
    return null;
  }
}

function progressHtml(id, message = "Ready", value = 0) {
  return `<div class="progress" id="${id}">
    <div class="track"><div class="fill" style="width:${Math.round(value * 100)}%"></div></div>
    <div class="msg">${esc(message)}</div>
  </div>`;
}

function updateProgress(id, job) {
  const box = document.getElementById(id);
  if (!box) return;
  const fill = box.querySelector(".fill");
  const msg = box.querySelector(".msg");
  if (fill) fill.style.width = `${Math.round((job.progress || 0) * 100)}%`;
  if (msg) msg.textContent = job.error || job.message || "Working…";
}

function pollJob(jobId, progressId, onDone) {
  return new Promise((resolve, reject) => {
    const tick = async () => {
      try {
        const job = await api(`/api/jobs/${jobId}`);
        updateProgress(progressId, job);
        if (job.status === "done") {
          resolve(job.result);
          if (onDone) onDone(job.result);
          return;
        }
        if (job.status === "error") {
          toast(job.error || "任务失败", "bad");
          reject(new Error(job.error || "任务失败"));
          return;
        }
        setTimeout(tick, 700);
      } catch (error) {
        reject(error);
      }
    };
    tick();
  });
}

/* --------------------------------------------------------------- overview */

function greeting() {
  const hour = new Date().getHours();
  if (hour < 5) return "night";
  if (hour < 12) return "morning";
  if (hour < 18) return "afternoon";
  return "evening";
}

function renderOverview() {
  const data = state.overview;
  if (!data) return `<div class="empty"><strong>正在读取工作台</strong>Zotero 与 Anki 状态加载中…</div>`;
  const due = data.anki?.connected ? data.anki.due : 0;
  const ringC = 2 * Math.PI * 30;
  const ringProgress = clamp(due / 50, 0, 1);
  const maxWeek = Math.max(1, ...data.week.map((d) => d.count));
  const last = data.lastReport;
  const recent = data.library.recent || [];
  const script = state.script?.text || "";
  const words = script ? script.replace(/^---[\s\S]*?---/, "").split(/\s+/).filter(Boolean).length : data.scriptWords;
  const minutes = Math.max(1, Math.round(words / 145));

  return `
  <div class="spectrum-line"></div>
  <div class="hero">
    <div class="hero-main">
      <div class="eyebrow">${new Date().toLocaleDateString("en-GB", { weekday: "long", day: "numeric", month: "long" })}</div>
      <div class="hero-title">Good ${greeting()}.<br><em>Make the paper speak.</em></div>
      <p class="hero-copy">从 Zotero 的一篇论文出发：读懂它，拆出可复用的句子，再用自己的声音讲三分钟。所有练习都留在本地。</p>
      <div class="hero-meta">
        <div><div class="num">${data.streak}</div><div class="lbl">day streak</div></div>
        <div><div class="num">${data.library.total}</div><div class="lbl">papers</div></div>
        <div><div class="num">${data.phrases}</div><div class="lbl">phrases</div></div>
        <div><div class="num">${data.sessions}</div><div class="lbl">sessions</div></div>
      </div>
    </div>
    <div class="hero-side">
      <div class="card review-card">
        <div class="card-head" style="padding:0">
          <div><div class="card-title">Review queue</div><div class="card-sub">${data.anki?.connected ? "AnkiConnect 已连接" : "Anki 尚未连接"}</div></div>
          <span class="pill ${data.anki?.connected ? "ok" : ""}">${data.anki?.connected ? "live" : "offline"}</span>
        </div>
        <div class="review-ring">
          <svg class="ring" viewBox="0 0 78 78">
            <circle cx="39" cy="39" r="30" fill="none" stroke="var(--track)" stroke-width="5"/>
            <circle cx="39" cy="39" r="30" fill="none" stroke="var(--coral)" stroke-width="5" stroke-linecap="round"
              stroke-dasharray="${(ringC * ringProgress).toFixed(1)} ${ringC}" transform="rotate(-90 39 39)"/>
            <text x="39" y="42" text-anchor="middle">${due}</text>
            <text x="39" y="53" text-anchor="middle"><tspan style="font-size:7px;fill:var(--faint)">DUE TODAY</tspan></text>
          </svg>
          <div class="review-nums">
            <span><b>${data.anki?.new ?? 0}</b> new</span>
            <span><b>${data.anki?.learning ?? 0}</b> learning</span>
            <span><b>${data.anki?.review ?? 0}</b> review</span>
          </div>
        </div>
        ${data.anki?.connected
          ? `<button class="quiet-btn" data-action="anki-launch">${icon("play")} 打开 Anki 复习</button>`
          : `<button class="primary-btn full-btn" data-action="anki-launch">${icon("zap")} 启动 Anki</button>`}
      </div>
      <div class="card review-card">
        <div class="card-head" style="padding:0">
          <div><div class="card-title">Next move</div><div class="card-sub">最短的下一步</div></div>
        </div>
        <div class="action-list">
          <button class="action-item" data-go="speak">${icon("mic")} 跟读今天的 3 分钟稿<span>${minutes} min</span></button>
          <button class="action-item" data-go="library">${icon("library")} 从文库挑一篇论文<span>${data.library.annotated} 篇有标注</span></button>
        </div>
      </div>
    </div>
  </div>

  <div class="spectrum-grid">
    <article class="spec-card coral" data-go="library">
      <div class="spec-top"><div class="spec-label">Read</div><span class="spec-icon">${icon("library")}</span></div>
      <div class="spec-value">${data.library.total} <span style="font-size:13px;color:var(--faint)">papers</span></div>
      <div class="spec-note">${data.library.annotated} 篇带有标注；标注会变成 Anki 卡片。</div>
      <div class="spec-link">打开文库 ${icon("arrow")}</div>
    </article>
    <article class="spec-card amber" data-go="write">
      <div class="spec-top"><div class="spec-label">Write</div><span class="spec-icon">${icon("pen")}</span></div>
      <div class="spec-value">${data.phrases} <span style="font-size:13px;color:var(--faint)">phrases</span></div>
      <div class="spec-note">按论证功能检索句型，再放进段落实验室里改写。</div>
      <div class="spec-link">打开句型库 ${icon("arrow")}</div>
    </article>
    <article class="spec-card teal" data-go="speak">
      <div class="spec-top"><div class="spec-label">Speak</div><span class="spec-icon">${icon("mic")}</span></div>
      <div class="spec-value">${last ? pct(last.contentWer ?? 0) : "—"} <span style="font-size:13px;color:var(--faint)">content WER</span></div>
      <div class="spec-note">${last ? `上次 ${last.duration}s · ${Math.round(last.wpm)} wpm · ${last.generated}` : "还没有录音分析。先听示范音，再录第一版。"}</div>
      <div class="spec-link">开始口语 ${icon("arrow")}</div>
    </article>
  </div>

  <div class="two-col">
    <div class="card panel">
      <div class="card-head">
        <div><div class="card-title">Recent papers</div><div class="card-sub">来自 Zotero 的只读快照</div></div>
        <button class="quiet-btn" data-go="library">全部 ${icon("arrow")}</button>
      </div>
      ${recent.map((item) => `
        <div class="paper-row" data-paper="${item.id}">
          <div class="paper-year">${esc(item.year || "—")}</div>
          <div style="min-width:0">
            <div class="paper-title">${esc(item.title)}</div>
            <div class="paper-meta">${esc(item.firstAuthor || "Unknown")}${item.publication ? " · " + esc(item.publication) : ""}${item.annotations ? ` · ${item.annotations} annotations` : ""}</div>
          </div>
        </div>`).join("") || `<div class="empty">Zotero 文库为空</div>`}
    </div>
    <div class="card panel">
      <div class="card-head"><div><div class="card-title">This week</div><div class="card-sub">${data.today} 次练习 · 今天</div></div></div>
      <div class="week">
        ${data.week.map((day) => `<div class="day"><div class="bar ${day.count ? "" : "zero"}" style="height:${day.count ? Math.max(8, (day.count / maxWeek) * 100) : 4}%" title="${day.date}: ${day.count}"></div><div class="d">${day.day}</div></div>`).join("")}
      </div>
      <div class="section-title" style="margin-bottom:6px"><h2>Latest</h2></div>
      <div class="action-list">
        ${(data.activity || []).slice(0, 4).map((row) => `<div class="action-item" style="cursor:default">${icon("spark")} ${esc(row.label)}<small>${esc(row.at.slice(11, 16))}</small></div>`).join("") || `<div class="faint" style="font-size:11.5px">完成一次练习后，这里会出现记录。</div>`}
      </div>
    </div>
  </div>`;
}

/* --------------------------------------------------------------- library */

function renderLibraryRows() {
  const box = document.getElementById("lib-rows");
  if (!box) return;
  const items = state.library.items;
  box.innerHTML = items.map((item) => `
    <button class="lib-row ${state.library.selected === item.id ? "active" : ""}" data-paper="${item.id}">
      <div class="t">${esc(item.title)}</div>
      <div class="m">
        <span>${esc(item.year || "—")}</span><span class="sep"></span>
        <span>${esc(item.firstAuthor || "Unknown")}</span>
        ${item.annotations ? `<span class="sep"></span><span>${item.annotations} notes</span>` : ""}
        ${item.pdfs ? `<span class="sep"></span><span>PDF</span>` : ""}
      </div>
    </button>`).join("") || `<div class="empty" style="margin:10px"><strong>没有匹配的文献</strong>换一个关键词，或在 Zotero 里刷新。</div>`;
}

function renderLibraryDetail() {
  const box = document.getElementById("lib-detail");
  if (!box) return;
  const item = state.library.detail;
  if (!item) {
    box.innerHTML = `<div class="empty" style="margin-top:60px"><strong>选择一篇论文</strong>左侧是 Zotero 文库；点开后可查看摘要、标注，并一键生成讲述稿。</div>`;
    return;
  }
  const anns = item.annotationList || [];
  box.innerHTML = `
    <div class="card-head" style="padding:0">
      <span class="pill coral">${esc(item.type)}</span>
      <span class="faint" style="font-size:10.5px">Added ${esc(item.added || "—")}</span>
    </div>
    <h2>${esc(item.title)}</h2>
    <div class="authors">${esc(item.authors.join(", ") || "Unknown authors")}</div>
    <div class="venue">${esc(item.publication || "—")}${item.year ? ` · ${esc(item.year)}` : ""}${item.doi ? ` · DOI ${esc(item.doi)}` : ""}</div>
    <div class="detail-actions">
      ${item.pdfs?.[0]?.exists ? `<button class="primary-btn" data-action="open-pdf" data-path="${esc(item.pdfs[0].path)}">${icon("book")} 打开 PDF</button>` : ""}
      <button class="ghost-btn" data-action="open-zotero" data-key="${esc(item.key)}">${icon("external")} 在 Zotero 中定位</button>
      <button class="ghost-btn" data-action="copy-cite">${icon("download")} 复制引用</button>
      <button class="ghost-btn" data-action="make-script" data-id="${item.id}">${icon("mic")} 生成讲述稿</button>
    </div>
    <div class="abstract">${esc(item.abstract || "这篇文献没有摘要。")}</div>
    ${item.tags?.length ? `<div class="tags">${item.tags.map((t) => `<span class="pill">${esc(t)}</span>`).join("")}</div>` : ""}
    <div class="meta-grid">
      <div><div class="k">Authors</div><div class="v">${esc(item.authors.length)} 位</div></div>
      <div><div class="k">Attachments</div><div class="v">${item.pdfs?.length || 0} PDF</div></div>
      <div><div class="k">Annotations</div><div class="v">${anns.length}</div></div>
      <div><div class="k">Collection</div><div class="v">${esc(item.collections.join(", ") || "—")}</div></div>
    </div>
    <div class="section-title"><h2>Annotations</h2><span>${anns.length} 条</span></div>
    ${anns.map((ann) => `
      <div class="ann">
        <q>${esc(ann.text || "(image highlight)")}</q>
        ${ann.comment ? `<div class="c">${esc(ann.comment)}</div>` : ""}
        <div class="p">${ann.page ? `p. ${esc(ann.page)}` : ""} ${esc(ann.color || "")}</div>
      </div>`).join("") || `<div class="empty" style="padding:26px"><strong>这篇论文还没有标注</strong>在 Zotero 阅读器里划词并翻译，Prism 下次刷新就能读到。</div>`}
  `;
}

async function openPaper(id, keepRoute = false) {
  state.library.selected = id;
  renderLibraryRows();
  const box = document.getElementById("lib-detail");
  if (box) box.innerHTML = `<div class="empty" style="margin-top:60px">正在读取…</div>`;
  try {
    state.library.detail = await api(`/api/library/${id}`);
    renderLibraryDetail();
  } catch (error) {
    if (box) box.innerHTML = `<div class="empty">${esc(error.message)}</div>`;
  }
  if (!keepRoute) return;
}

async function renderLibrary() {
  const view = document.getElementById("view");
  view.innerHTML = `
    <div class="spectrum-line"></div>
    <div class="library-grid">
      <div class="card lib-list">
        <div class="lib-toolbar">
          <label class="search-box">${icon("search")}<input id="lib-search" placeholder="搜索标题、作者、期刊…" value="${esc(state.library.q)}"></label>
          <button class="quiet-btn" data-action="library-refresh" title="刷新 Zotero 快照">${icon("refresh")}</button>
        </div>
        <div class="lib-rows" id="lib-rows"></div>
      </div>
      <div class="card detail" id="lib-detail"></div>
    </div>`;
  renderLibraryRows();
  renderLibraryDetail();
  const search = document.getElementById("lib-search");
  let timer;
  search.addEventListener("input", () => {
    clearTimeout(timer);
    timer = setTimeout(async () => {
      state.library.q = search.value;
      const data = await api(`/api/library?q=${encodeURIComponent(search.value)}&limit=100`);
      state.library.items = data.items;
      renderLibraryRows();
    }, 220);
  });
  if (!state.library.items.length) {
    const data = await api("/api/library?limit=100");
    state.library.items = data.items;
    renderLibraryRows();
  }
  if (!state.library.selected && state.library.items.length) {
    state.library.selected = state.library.items[0].id;
  }
  if (state.library.selected) openPaper(state.library.selected, true);
}

async function makeScript(detail) {
  const title = detail.title;
  const authors = detail.authors.join(", ");
  const text = `---
title: ${title}
source: ${authors} (${detail.year})
---

Good morning. Today I want to talk about "${title}".

Why does this paper matter? ${detail.abstract ? detail.abstract.split(". ").slice(0, 2).join(". ") + "." : "Start with the problem the authors were trying to solve."}

Let me walk you through the approach. The authors [[describe the key method here]], and the central measurement is [[the result you want the audience to remember]].

What is the evidence? First, [[evidence one]]. Second, [[evidence two]]. The figure that carries the argument is [[figure or panel]].

Two caveats. First, [[limitation one]]. Second, [[limitation two]].

The takeaway is this. [[One sentence that states what changed because of this paper.]]

Thank you. I am happy to take questions.
`;
  const name = `paper-${detail.id}.md`;
  await api("/api/script", { method: "PUT", body: JSON.stringify({ name, text }) });
  state.script = { name, text };
  state.scripts = [];
  toast("讲述稿已生成，正在打开 Speak", "ok");
  setRoute("speak");
}

/* --------------------------------------------------------------- speak */

function scriptMeta(text) {
  const clean = text.replace(/^---[\s\S]*?---/, "");
  const words = clean.split(/\s+/).filter(Boolean).length;
  return { words, minutes: Math.max(1, Math.round(words / 145)) };
}

function renderSpeakSide() {
  const box = document.getElementById("speak-side");
  if (!box) return;
  const tab = state.speakTab;
  const report = state.report;
  let body = "";
  if (tab === "listen") {
    body = `
      <div class="tab-body">
        <h3>示范音</h3>
        <p class="hint">Kokoro 先给你一个可模仿的目标。first run 会下载模型到 E 盘，之后离线可用。</p>
        <div class="field"><label>Voice</label>
          <select id="tts-voice">
            <option value="af_heart">af_heart · 女声</option>
            <option value="af_bella">af_bella · 女声</option>
            <option value="am_michael">am_michael · 男声</option>
            <option value="bf_emma">bf_emma · 英音女声</option>
          </select>
        </div>
        <div class="field"><label>Speed · <span id="speed-val">0.95</span></label>
          <input type="range" id="tts-speed" min="0.75" max="1.15" step="0.01" value="0.95">
        </div>
        <button class="primary-btn full-btn" id="tts-btn">${icon("speaker")} 生成示范音</button>
        <div id="tts-progress">${state.tts ? "" : progressHtml("tts-prog", "等待生成", 0)}</div>
        ${state.tts ? `<div class="audio-box">
          <audio controls src="${esc(state.tts.url)}"></audio>
          <div class="faint" style="margin-top:8px;font-size:10.5px">${state.tts.duration.toFixed(1)} s · ${esc(state.tts.voice)} · speed ${state.tts.speed}${state.tts.cached ? " · cached" : ""}</div>
        </div>` : ""}
      </div>`;
  } else if (tab === "terms") {
    if (!state.links) {
      body = `<div class="tab-body"><div class="empty" style="padding:30px">正在检索 [[...]] 标记…</div></div>`;
    } else {
      body = `
        <div class="tab-body">
          <h3>YouGlish 语境</h3>
          <p class="hint">点击“听”打开真人语境。每个词听 3 个片段：跟读、只听节奏、自己复述。</p>
          <div class="link-list">
            ${state.links.map((row) => `<div class="link-row">
              <a href="${esc(row.url)}" data-action="open-url" data-url="${esc(row.url)}">听 ${icon("external")}</a>
              <div class="term">${esc(row.term)}</div>
              <div class="ctx">${esc(row.context || "—")}</div>
            </div>`).join("") || `<div class="empty">没有标记。在稿子里用 [[term]] 包住想练的词。</div>`}
          </div>
          <details style="margin-top:14px">
            <summary class="faint" style="cursor:pointer;font-size:11px">术语读法表</summary>
            <div style="margin-top:8px">${(state.pronunciation || []).map((t) => `<div class="preview-row"><span class="w">${esc(t.term)}</span><span class="tr">${esc(t.say)}</span></div>`).join("")}</div>
          </details>
        </div>`;
    }
  } else {
    body = renderAnalyzeTab(report);
  }
  box.innerHTML = `
    <div class="tabs">
      <button class="tab ${tab === "listen" ? "active" : ""}" data-tab="listen">Listen</button>
      <button class="tab ${tab === "terms" ? "active" : ""}" data-tab="terms">Terms</button>
      <button class="tab ${tab === "analyze" ? "active" : ""}" data-tab="analyze">Analyze</button>
    </div>
    <div class="card">${body}</div>`;
  mountIcons(box);
  bindSpeakSide();
  if (tab === "analyze" && report) drawReportChart(report);
}

function renderAnalyzeTab(report) {
  if (!report) {
    return `<div class="tab-body">
      <h3>录音复盘</h3>
      <p class="hint">录 60–90 秒，上传 wav 或 m4a。Whisper 对齐脚本，Praat 测量语速、停顿和音高。</p>
      <label class="dropzone" id="dropzone">
        <input type="file" id="audio-file" accept="audio/*" hidden>
        <strong id="file-name">选择或拖入录音</strong>
        <span>wav / m4a / mp3 · 建议同一设备、同一房间</span>
      </label>
      <div style="height:12px"></div>
      <button class="primary-btn full-btn" id="analyze-btn" disabled>${icon("wave")} 开始分析</button>
      <div id="analyze-progress"></div>
      <p class="hint" style="margin-top:14px">第一次会下载 Whisper base.en（约 150 MB）到 E 盘。</p>
    </div>`;
  }
  const asrFailed = Boolean(report.asrNote);
  const werTone = asrFailed ? "" : (report.contentWer ?? 0) > 0.25 ? "bad" : (report.contentWer ?? 0) > 0.12 ? "warn" : "good";
  return `<div class="tab-body">
    <div class="card-head" style="padding:0"><div><h3 style="margin:0">最近一次复盘</h3><p class="hint" style="margin:4px 0 0">${esc(report.generated)} · ${esc(report.model)}</p></div><span class="pill ${werTone === "good" ? "ok" : ""}">${asrFailed ? "no transcript" : werTone}</span></div>
    ${asrFailed ? `<p class="hint" style="color:var(--bad);margin:0 0 12px">${esc(report.asrNote)}<br>声学指标仍然有效；WER 与缺失词本轮不作结论。</p>` : ""}
    <div class="metric-grid">
      <div class="metric ${werTone}"><div class="k">Content WER</div><div class="v">${asrFailed ? "—" : pct((report.contentWer ?? 0))}</div></div>
      <div class="metric"><div class="k">Speaking rate</div><div class="v">${Math.round(report.wpm)}<small>wpm</small></div></div>
      <div class="metric"><div class="k">Pauses</div><div class="v">${(report.pauses || []).length}<small>${report.pauseRate}/min</small></div></div>
      <div class="metric"><div class="k">Pitch range</div><div class="v">${Math.round(report.pitchRange)}<small>Hz</small></div></div>
    </div>
    <canvas class="chart" id="report-chart"></canvas>
    <div class="legend"><span><i style="background:var(--teal)"></i>waveform</span><span><i style="background:var(--coral)"></i>pitch</span><span>${(report.duration ?? 0).toFixed(1)}s · ${report.refWords ?? 0} words</span></div>
    <ul class="actions-list">${(report.actions || []).map((action, i) => `<li><span class="n">${i + 1}</span><span>${esc(action)}</span></li>`).join("")}</ul>
    ${report.issues?.length ? `<div class="section-title" style="margin-bottom:0"><h2>Differences</h2><span>${report.issues.length}</span></div>
      <table class="issue-table">${report.issues.slice(0, 6).map((i) => `<tr><td>${esc(i.ref || "—")}</td><td>${esc(i.hyp || "—")}</td><td>${esc(i.type)}</td></tr>`).join("")}</table>` : ""}
    ${report.terms?.length ? `<div style="margin-top:12px"><div class="k faint" style="font-size:9.5px;letter-spacing:.12em">TERMS TO RE-CHECK</div><div class="tags" style="margin-top:6px">${report.terms.map((t) => `<span class="pill teal">${esc(t)}</span>`).join("")}</div></div>` : ""}
    <div class="audio-box" style="margin-top:12px"><audio controls src="${esc(report.audioUrl)}"></audio></div>
    <button class="ghost-btn full-btn" id="new-take" style="margin-top:10px">${icon("refresh")} 录下一版</button>
  </div>`;
}

function drawReportChart(report) {
  const canvas = document.getElementById("report-chart");
  if (!canvas) return;
  const dpr = window.devicePixelRatio || 1;
  const width = canvas.clientWidth || 340;
  const height = 92;
  canvas.width = width * dpr;
  canvas.height = height * dpr;
  const ctx = canvas.getContext("2d");
  ctx.scale(dpr, dpr);
  ctx.clearRect(0, 0, width, height);
  const wave = report.waveform || [];
  const pitch = report.pitch || [];
  if (wave.length) {
    ctx.beginPath();
    wave.forEach((v, i) => {
      const x = (i / (wave.length - 1)) * width;
      const y = height / 2 - v * (height * 0.36);
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    });
    ctx.strokeStyle = "rgba(131,183,168,.65)";
    ctx.lineWidth = 1;
    ctx.stroke();
  }
  if (pitch.length) {
    ctx.beginPath();
    let started = false;
    pitch.forEach((v, i) => {
      const x = (i / (pitch.length - 1)) * width;
      if (v === null) { started = false; return; }
      const y = height - 8 - v * (height - 16);
      if (!started) { ctx.moveTo(x, y); started = true; } else ctx.lineTo(x, y);
    });
    ctx.strokeStyle = "rgba(232,160,145,.85)";
    ctx.lineWidth = 1.4;
    ctx.stroke();
  }
}

function bindSpeakSide() {
  document.querySelectorAll("[data-tab]").forEach((btn) => {
    btn.onclick = () => {
      state.speakTab = btn.dataset.tab;
      if (state.speakTab === "terms" && !state.links) loadLinks();
      renderSpeakSide();
    };
  });
  const speed = document.getElementById("tts-speed");
  if (speed) speed.oninput = () => { document.getElementById("speed-val").textContent = speed.value; };
  const ttsBtn = document.getElementById("tts-btn");
  if (ttsBtn) ttsBtn.onclick = generateTts;
  const analyzeBtn = document.getElementById("analyze-btn");
  const file = document.getElementById("audio-file");
  if (file) {
    file.onchange = () => {
      const name = file.files[0]?.name;
      if (name) {
        document.getElementById("file-name").textContent = name;
        analyzeBtn.disabled = false;
      }
    };
    const zone = document.getElementById("dropzone");
    zone.ondragover = (e) => { e.preventDefault(); zone.classList.add("over"); };
    zone.ondragleave = () => zone.classList.remove("over");
    zone.ondrop = (e) => {
      e.preventDefault();
      zone.classList.remove("over");
      if (e.dataTransfer.files[0]) {
        file.files = e.dataTransfer.files;
        file.dispatchEvent(new Event("change"));
      }
    };
  }
  if (analyzeBtn) analyzeBtn.onclick = startAnalysis;
  const newTake = document.getElementById("new-take");
  if (newTake) newTake.onclick = () => { state.report = null; state.speakTab = "analyze"; renderSpeakSide(); };
}

async function loadLinks() {
  const text = document.getElementById("script-editor")?.value || state.script.text;
  try {
    const [links, pronunciation] = await Promise.all([
      api(`/api/speak/links?text=${encodeURIComponent(text)}&all=true`),
      api("/api/speak/pronunciation")
    ]);
    state.links = links.links;
    state.pronunciation = pronunciation.terms;
  } catch (error) {
    toast(error.message, "bad");
    state.links = [];
  }
  renderSpeakSide();
}

async function generateTts() {
  const btn = document.getElementById("tts-btn");
  if (!btn) return;
  btn.disabled = true;
  const box = document.getElementById("tts-progress");
  if (box) box.innerHTML = progressHtml("tts-prog", "提交任务…", 0);
  const text = document.getElementById("script-editor")?.value || state.script.text;
  try {
    const { jobId } = await api("/api/speak/tts", {
      method: "POST",
      body: JSON.stringify({
        text,
        voice: document.getElementById("tts-voice").value,
        speed: Number(document.getElementById("tts-speed").value)
      })
    });
    const result = await pollJob(jobId, "tts-prog");
    state.tts = result;
    toast(`示范音已生成 · ${result.duration.toFixed(1)} s`, "ok");
    renderSpeakSide();
  } catch (error) {
    btn.disabled = false;
    toast(error.message, "bad");
  }
}

async function startAnalysis() {
  const file = document.getElementById("audio-file")?.files?.[0];
  if (!file) return;
  const btn = document.getElementById("analyze-btn");
  btn.disabled = true;
  const box = document.getElementById("analyze-progress");
  if (box) box.innerHTML = progressHtml("analyze-prog", "上传录音…", 0.02);
  const form = new FormData();
  form.append("audio", file);
  form.append("text", document.getElementById("script-editor")?.value || state.script.text);
  form.append("model", state.settings?.speech?.whisper_model || "base.en");
  try {
    const { jobId } = await api("/api/speak/analyze", { method: "POST", body: form });
    const result = await pollJob(jobId, "analyze-prog");
    state.report = result;
    toast(`分析完成 · WER ${pct(result.wer)}`, "ok");
    renderSpeakSide();
  } catch (error) {
    btn.disabled = false;
    toast(error.message, "bad");
  }
}

async function renderSpeak() {
  const view = document.getElementById("view");
  if (!state.scripts.length) {
    const data = await api("/api/scripts");
    state.scripts = data.scripts;
  }
  if (!state.script.text) {
    const data = await api("/api/script?name=sample_talk.md");
    state.script = { name: data.name, text: data.text };
  }
  if (state.report === null) {
    try {
      const report = await api("/api/speak/report");
      state.report = report && report.generated ? report : null;
    } catch (_) { state.report = null; }
  }
  const meta = scriptMeta(state.script.text);
  view.innerHTML = `
    <div class="spectrum-line"></div>
    <div class="speak-grid">
      <div class="card script-wrap">
        <div class="script-bar">
          <select id="script-select">
            ${state.scripts.map((s) => `<option value="${esc(s.name)}" ${s.name === state.script.name ? "selected" : ""}>${esc(s.title)}</option>`).join("")}
          </select>
          <span class="pill ${state.script.name.startsWith("paper-") ? "teal" : "coral"}">${state.script.name.startsWith("paper-") ? "from library" : "sample"}</span>
          <div class="script-stats"><span id="word-count">${meta.words} words</span><span>≈ ${meta.minutes} min</span></div>
          <button class="quiet-btn" id="save-script">${icon("save")} 保存</button>
        </div>
        <textarea class="script-editor" id="script-editor" spellcheck="false">${esc(state.script.text)}</textarea>
        <div class="term-strip" id="term-strip"></div>
      </div>
      <div class="side-panel" id="speak-side"></div>
    </div>`;
  mountIcons(view);
  const editor = document.getElementById("script-editor");
  const updateMeta = () => {
    state.script.text = editor.value;
    const info = scriptMeta(editor.value);
    document.getElementById("word-count").textContent = `${info.words} words`;
    const terms = [...new Set([...editor.value.matchAll(/\[\[([^\]]+)\]\]/g)].map((m) => m[1]))];
    document.getElementById("term-strip").innerHTML = terms.length
      ? terms.map((t) => `<span class="pill amber">${esc(t)}</span>`).join("")
      : `<span class="faint" style="font-size:10.5px">用 [[term]] 标记想练的词，Terms 面板会生成 YouGlish 链接。</span>`;
  };
  editor.addEventListener("input", updateMeta);
  updateMeta();
  document.getElementById("script-select").onchange = async (event) => {
    const data = await api(`/api/script?name=${encodeURIComponent(event.target.value)}`);
    state.script = { name: data.name, text: data.text };
    state.links = null;
    state.tts = null;
    renderSpeak();
  };
  document.getElementById("save-script").onclick = async () => {
    try {
      const name = state.script.name.startsWith("paper-") ? state.script.name : "working.md";
      await api("/api/script", { method: "PUT", body: JSON.stringify({ name, text: editor.value }) });
      state.script.name = name;
      toast("脚本已保存到 data/scripts", "ok");
    } catch (error) { toast(error.message, "bad"); }
  };
  renderSpeakSide();
}

/* --------------------------------------------------------------- write */

function phraseListHtml() {
  const q = state.phraseFilter.toLowerCase();
  const rows = state.phrases.filter((p) => !q || Object.values(p).join(" ").toLowerCase().includes(q));
  return rows.map((p) => `<div class="phrase" data-phrase="${p.id}">
    <div class="f">${esc(p.function)}</div>
    <div class="tpl">${esc(p.template)}</div>
    <div class="zh">${esc(p.chinese_cue)}</div>
  </div>`).join("") || `<div class="empty">没有匹配的句型</div>`;
}

function checkPanel() {
  const result = state.writeCheck;
  if (!result) return `<div class="empty" style="padding:30px"><strong>还没有检查</strong>写完一段后点“检查段落”，Prism 会给出可执行的修改项。</div>`;
  const stats = result.stats || {};
  return `
    <div class="check-summary">
      <div><div class="n">${stats.words ?? 0}</div><div class="l">words</div></div>
      <div><div class="n">${stats.avgSentence ?? 0}</div><div class="l">avg sentence</div></div>
      <div><div class="n" style="color:${stats.errors ? "var(--bad)" : "var(--ok)"}">${stats.errors ?? 0}</div><div class="l">errors</div></div>
      <div><div class="n" style="color:${stats.warnings ? "var(--warn)" : "var(--ok)"}">${stats.warnings ?? 0}</div><div class="l">warnings</div></div>
      <div style="margin-left:auto;align-self:center"><span class="pill">${esc(result.engine)}</span></div>
    </div>
    ${(result.issues || []).map((issue) => `<div class="issue">
      <span class="sev ${esc(issue.severity)}"></span>
      <div><div>${esc(issue.message)}</div><div class="faint" style="margin-top:2px">line ${issue.line}${issue.suggestion ? ` · 建议 ${esc(issue.suggestion)}` : ""}</div></div>
      <span class="rule">${esc(issue.rule)}</span>
    </div>`).join("") || `<div class="empty" style="padding:24px"><strong>没有发现问题</strong>仍然要找一位真人读者。</div>`}`;
}

function renderWrite() {
  const view = document.getElementById("view");
  view.innerHTML = `
    <div class="spectrum-line"></div>
    <div class="write-grid">
      <div class="card">
        <div class="card-head"><div><div class="card-title">Phrasebank</div><div class="card-sub">按论证功能检索，不是按语法</div></div><span class="pill amber">${state.phrases.length}</span></div>
        <div class="chips" id="phrase-chips"></div>
        <div class="lib-toolbar" style="border-top:0;border-bottom:1px solid var(--line-soft)">
          <label class="search-box">${icon("search")}<input id="phrase-search" placeholder="搜索功能、中文意图、句型…" value="${esc(state.phraseFilter)}"></label>
        </div>
        <div class="phrase-list" id="phrase-list"></div>
      </div>
      <div>
        <div class="card">
          <div class="card-head"><div><div class="card-title">Paragraph lab</div><div class="card-sub">先写自己的版本，再让规则介入</div></div><span class="pill" id="lab-count">0 words</span></div>
          <textarea class="lab-editor" id="lab-editor" placeholder="Write one paragraph you actually need: an introduction, a result, or a reviewer response…">${esc(state.writeText)}</textarea>
          <div class="lab-foot">
            <span>点击左侧句型可插入到光标处</span>
            <span class="spacer"></span>
            <button class="primary-btn" id="check-btn">${icon("check")} 检查段落</button>
          </div>
        </div>
        <div class="card" style="margin-top:14px">
          <div class="card-head"><div><div class="card-title">Findings</div><div class="card-sub">只修前三项，重写同一段</div></div></div>
          <div style="padding:0 18px 18px" id="check-panel">${checkPanel()}</div>
        </div>
      </div>
    </div>`;
  mountIcons(view);
  const chips = document.getElementById("phrase-chips");
  const sections = [...new Set(state.phrases.map((p) => p.section))];
  chips.innerHTML = `<button class="chip ${!state.phraseFilter ? "active" : ""}" data-section="">All</button>` +
    sections.map((s) => `<button class="chip ${state.phraseFilter === s ? "active" : ""}" data-section="${esc(s)}">${esc(s)}</button>`).join("");
  chips.querySelectorAll("[data-section]").forEach((chip) => {
    chip.onclick = () => { state.phraseFilter = chip.dataset.section; renderWrite(); };
  });
  document.getElementById("phrase-list").innerHTML = phraseListHtml();
  document.getElementById("phrase-list").querySelectorAll("[data-phrase]").forEach((card) => {
    card.onclick = () => {
      const phrase = state.phrases.find((p) => String(p.id) === card.dataset.phrase);
      const editor = document.getElementById("lab-editor");
      const start = editor.selectionStart;
      editor.value = editor.value.slice(0, start) + phrase.template + editor.value.slice(editor.selectionEnd);
      editor.focus();
      editor.selectionStart = editor.selectionEnd = start + phrase.template.length;
      state.writeText = editor.value;
      updateLabCount();
      toast("句型已插入", "ok");
    };
  });
  const search = document.getElementById("phrase-search");
  search.addEventListener("input", () => {
    state.phraseFilter = search.value;
    document.getElementById("phrase-list").innerHTML = phraseListHtml();
    document.getElementById("phrase-list").querySelectorAll("[data-phrase]").forEach((card) => {
      card.onclick = () => {
        const phrase = state.phrases.find((p) => String(p.id) === card.dataset.phrase);
        const editor = document.getElementById("lab-editor");
        const start = editor.selectionStart;
        editor.value = editor.value.slice(0, start) + phrase.template + editor.value.slice(editor.selectionEnd);
        state.writeText = editor.value;
        updateLabCount();
      };
    });
  });
  const editor = document.getElementById("lab-editor");
  editor.addEventListener("input", () => { state.writeText = editor.value; updateLabCount(); });
  function updateLabCount() {
    const words = editor.value.split(/\s+/).filter(Boolean).length;
    document.getElementById("lab-count").textContent = `${words} words`;
  }
  updateLabCount();
  document.getElementById("check-btn").onclick = async () => {
    const btn = document.getElementById("check-btn");
    btn.disabled = true;
    try {
      state.writeCheck = await api("/api/write/check", { method: "POST", body: JSON.stringify({ text: editor.value }) });
      document.getElementById("check-panel").innerHTML = checkPanel();
      toast("检查完成", "ok");
    } catch (error) { toast(error.message, "bad"); }
    btn.disabled = false;
  };
}

/* --------------------------------------------------------------- vocab */

async function loadVocab() {
  const [status, preview] = await Promise.all([
    api("/api/anki/status"),
    api("/api/anki/preview").catch(() => ({ notes: [], count: 0 }))
  ]);
  state.anki = status;
  state.preview = preview.notes || [];
  setAnkiChip(status);
}

function renderVocab() {
  const view = document.getElementById("view");
  const anki = state.anki || { connected: false };
  const notes = state.preview || [];
  view.innerHTML = `
    <div class="spectrum-line"></div>
    <div class="vocab-top">
      <div class="card stat-card"><div class="k">AnkiConnect</div><div class="v" style="color:${anki.connected ? "var(--ok)" : "var(--bad)"}">${anki.connected ? "Live" : "Offline"}</div><div class="s">${esc(anki.url || "")}</div></div>
      <div class="card stat-card"><div class="k">Due today</div><div class="v">${anki.connected ? anki.due : "—"}</div><div class="s">${anki.connected ? `${anki.new} new · ${anki.learning} learning · ${anki.review} review` : "启动 Anki 后读取"}</div></div>
      <div class="card stat-card"><div class="k">Zotero annotations</div><div class="v">${notes.length}</div><div class="s">带翻译的标注，可一键制卡</div></div>
      <div class="card stat-card"><div class="k">Decks</div><div class="v">${anki.connected ? anki.decks.length : 3}</div><div class="s">${esc((anki.decks || ["Prism::Vocab", "Prism::Phrases", "Prism::Listening"]).join(" · "))}</div></div>
    </div>

    <div class="vocab-grid">
      <div class="card panel">
        <div class="card-head"><div><div class="card-title">Review decks</div><div class="card-sub">学习记录留在 Anki，Prism 只读取统计</div></div><span class="pill ${anki.connected ? "ok" : ""}">${anki.connected ? "connected" : "offline"}</span></div>
        ${(anki.decks || ["Prism::Vocab", "Prism::Phrases", "Prism::Listening"]).map((deck) => `
          <div class="deck-row">
            <span class="ico" style="color:var(--coral)">${icon("layers")}</span>
            <div><div class="nm">${esc(deck)}</div><div class="pth">Prism</div></div>
            <span class="status"><span class="pill ${anki.connected ? "ok" : ""}">${anki.connected ? (anki.missingDecks?.includes(deck) ? "missing" : "ready") : "—"}</span></span>
          </div>`).join("")}
        <div class="btn-row" style="margin-top:16px">
          <button class="primary-btn" data-action="anki-launch">${icon("play")} 启动 Anki</button>
          <button class="ghost-btn" data-action="anki-setup">${icon("zap")} 初始化牌组</button>
          <button class="ghost-btn" data-action="anki-refresh">${icon("refresh")} 刷新</button>
        </div>
        <div id="vocab-progress"></div>
      </div>

      <div class="card panel">
        <div class="card-head"><div><div class="card-title">Export annotations</div><div class="card-sub">Zotero 只读快照 → Anki 卡片</div></div><span class="pill coral">${notes.length}</span></div>
        <div class="preview-row" style="border-top:0"><span class="w faint">Word</span><span class="tr faint">Translation</span><span class="src faint">Source</span></div>
        ${notes.slice(0, 7).map((n) => `<div class="preview-row"><span class="w">${esc(n.word.slice(0, 40))}</span><span class="tr">${esc(n.translation.slice(0, 30))}</span><span class="src">${esc(n.source)}</span></div>`).join("") || `<div class="empty" style="padding:24px"><strong>还没有带翻译的标注</strong>在 Zotero 里划词并翻译后再来。</div>`}
        <div class="btn-row" style="margin-top:16px">
          <button class="primary-btn" data-action="anki-export">${icon("download")} 导出到 Anki</button>
          <button class="ghost-btn" data-action="anki-export-all">${icon("plus")} 包含未翻译</button>
        </div>
        <p class="faint" style="font-size:10.5px;line-height:1.6;margin:12px 0 0">重复项会被跳过；导入状态保存在 <span class="mono">data/anki_state.json</span>。</p>
      </div>
    </div>

    <div class="steps">
      <div class="card step"><div class="n">01</div><div class="t">Read &amp; highlight</div><div class="d">在 Zotero 里划词，PDF Translate 把译文写进注释。Prism 读取只读快照，不碰原库。</div></div>
      <div class="card step"><div class="n">02</div><div class="t">Export</div><div class="d">点击导出，AnkiConnect 把词、译文、来源和回链写成卡片；已导出的自动跳过。</div></div>
      <div class="card step"><div class="n">03</div><div class="t">Review</div><div class="d">每天按到期队列复习 10–15 分钟。Prism 的首页会显示 due 数，也可以注册 Windows 提醒。</div></div>
    </div>`;
  mountIcons(view);
}

async function runAnkiAction(kind) {
  const box = document.getElementById("vocab-progress");
  if (box) box.innerHTML = progressHtml("vocab-prog", "连接 Anki…", 0.05);
  try {
    if (kind === "launch") {
      await api("/api/anki/launch", { method: "POST" });
      toast("Anki 已启动", "ok");
      await loadVocab();
      renderVocab();
      return;
    }
    if (kind === "setup") {
      const { jobId } = await api("/api/anki/setup", { method: "POST" });
      await pollJob(jobId, "vocab-prog");
      toast("牌组与句型卡已就绪", "ok");
    } else {
      const includeUntranslated = kind === "export-all";
      const { jobId } = await api("/api/anki/export", { method: "POST", body: JSON.stringify({ includeUntranslated }) });
      const result = await pollJob(jobId, "vocab-prog");
      toast(result.message || "导出完成", "ok");
    }
    await loadVocab();
    renderVocab();
    bindDynamic();
  } catch (error) {
    toast(error.message, "bad");
  }
}

/* --------------------------------------------------------------- settings */

function renderSettings() {
  const view = document.getElementById("view");
  const cfg = state.settings || {};
  const tools = state.tools || { rows: [] };
  view.innerHTML = `
    <div class="spectrum-line"></div>
    <div class="settings-grid">
      <div class="card settings-section">
        <h3>Connections</h3>
        <p class="desc">默认值在 config.json；本机改动写入不提交的 config.local.json。</p>
        <div class="field-row"><label>AnkiConnect</label><input id="set-anki-url" value="${esc(cfg.anki?.url || "")}"></div>
        <div class="field-row"><label>anki.exe</label><input id="set-anki-exe" value="${esc(cfg.system?.anki_exe || "")}"></div>
        <div class="field-row"><label>Zotero DB</label><input id="set-zotero" value="${esc(cfg.zotero?.db || "")}"></div>
        <div class="field-row"><label>Kokoro voice</label>
          <select id="set-voice">
            ${["af_heart", "af_bella", "am_michael", "bf_emma"].map((v) => `<option ${cfg.speech?.kokoro_voice === v ? "selected" : ""}>${v}</option>`).join("")}
          </select>
        </div>
        <div class="field-row"><label>Whisper model</label>
          <select id="set-whisper">
            ${["tiny.en", "base.en", "small.en", "medium.en"].map((v) => `<option ${cfg.speech?.whisper_model === v ? "selected" : ""}>${v}</option>`).join("")}
          </select>
        </div>
        <button class="primary-btn" id="save-settings">${icon("save")} 保存设置</button>
        <div class="folder-row" style="margin-top:16px">
          <button class="ghost-btn" data-action="open-folder" data-kind="data">${icon("folder")} data</button>
          <button class="ghost-btn" data-action="open-folder" data-kind="models">${icon("folder")} models</button>
          <button class="ghost-btn" data-action="open-folder" data-kind="tools">${icon("folder")} tools</button>
        </div>
      </div>

      <div class="card settings-section">
        <h3>Toolchain</h3>
        <p class="desc">E 盘工作区：${esc(tools.suite || "E:/LumenSuite")} · 模型 ${esc(tools.models || "—")} · Python ${esc(tools.python || "")}</p>
        ${(tools.rows || []).map((row) => `<div class="tool-row">
          <span class="st ${row.ok ? "ok" : "bad"}"></span>
          <div style="min-width:0"><div class="nm">${esc(row.name)}</div><div class="p">${esc(row.path)}</div></div>
          <div class="dt">${esc(row.detail)}</div>
        </div>`).join("")}
        <div class="faint" style="font-size:10.5px;line-height:1.6;margin-top:14px">缺失的项不会阻塞其他功能；写作检查会自动退回内置规则。</div>
      </div>

      <div class="card settings-section">
        <h3>About Prism</h3>
        <p class="desc">本地优先的论文英语工作台。Lumen 收书，Prism 拆光：读、写、说三条线共用一个界面。</p>
        <div class="meta-grid" style="border-top:0">
          <div><div class="k">Version</div><div class="v">0.3.0 · beta</div></div>
          <div><div class="k">Data</div><div class="v">全部本地</div></div>
          <div><div class="k">Code</div><div class="v">MIT</div></div>
          <div><div class="k">Docs</div><div class="v">CC BY-NC 4.0</div></div>
        </div>
      </div>

      <div class="card settings-section">
        <h3>Appearance</h3>
        <p class="desc">深色适合夜间读写，浅色适合白天和投影。选择会记在本机。</p>
        <div class="btn-row">
          <button class="chip ${currentTheme() === "dark" ? "active" : ""}" data-theme-choice="dark">${icon("moon")} 深色</button>
          <button class="chip ${currentTheme() === "light" ? "active" : ""}" data-theme-choice="light">${icon("sun")} 浅色</button>
        </div>
      </div>

      <div class="card settings-section">
        <h3>Shortcuts</h3>
        <p class="desc">少点几次鼠标。</p>
        <div class="deck-row"><span class="nm">Quick actions</span><span class="status"><kbd>Ctrl K</kbd></span></div>
        <div class="deck-row"><span class="nm">Close palette</span><span class="status"><kbd>Esc</kbd></span></div>
        <div class="deck-row"><span class="nm">Start session</span><span class="status"><kbd>Ctrl ↵</kbd></span></div>
        <div class="deck-row"><span class="nm">Open Anki</span><span class="status"><kbd>Ctrl Shift A</kbd></span></div>
      </div>
    </div>`;
  mountIcons(view);
  document.getElementById("save-settings").onclick = async () => {
    try {
      const saved = await api("/api/settings", {
        method: "PUT",
        body: JSON.stringify({
          ankiUrl: document.getElementById("set-anki-url").value,
          ankiExe: document.getElementById("set-anki-exe").value,
          zoteroDb: document.getElementById("set-zotero").value,
          voice: document.getElementById("set-voice").value,
          whisper: document.getElementById("set-whisper").value
        })
      });
      state.settings = saved.config;
      toast("设置已保存", "ok");
      refreshAnkiChip();
    } catch (error) { toast(error.message, "bad"); }
  };
  view.querySelectorAll("[data-theme-choice]").forEach((btn) => {
    btn.onclick = () => { applyTheme(btn.dataset.themeChoice); renderSettings(); };
  });
}

/* --------------------------------------------------------------- routing */

const ROUTES = {
  overview: { title: "Overview", sub: "你的论文英语工作台", render: renderOverview, load: async () => { state.overview = await api("/api/overview"); } },
  library: { title: "Library", sub: "Zotero 只读文库 · 标注即素材", render: renderLibrary, load: async () => {} },
  speak: { title: "Speak", sub: "示范音 · 跟读 · 录音复盘", render: renderSpeak, load: async () => {} },
  write: { title: "Write", sub: "句型库 · 段落实验室 · Vale 检查", render: renderWrite, load: async () => { if (!state.phrases.length) state.phrases = (await api("/api/write/phrases")).phrases; } },
  vocab: { title: "Vocab", sub: "Zotero 标注 → Anki 复习", render: renderVocab, load: async () => { await loadVocab(); } },
  settings: { title: "Settings", sub: "连接、路径与工具链", render: renderSettings, load: async () => { [state.settings, state.tools] = await Promise.all([api("/api/settings"), api("/api/tools/status")]); } }
};

async function route() {
  const [name, sub] = (location.hash.replace(/^#\//, "") || "overview").split("?")[0].split("/");
  const key = ROUTES[name] ? name : "overview";
  if (key === "speak" && sub === "analyze") state.speakTab = "analyze";
  state.route = key;
  markNav(key);
  const meta = ROUTES[key];
  document.getElementById("page-title").textContent = meta.title;
  document.getElementById("page-sub").textContent = meta.sub;
  const view = document.getElementById("view");
  view.innerHTML = `<div class="empty" style="margin-top:40px"><strong>正在加载</strong>读取本地数据…</div>`;
  try {
    await meta.load();
    const html = await meta.render();
    if (typeof html === "string") view.innerHTML = html;
    mountIcons(view);
    bindDynamic();
    if (key === "overview" && state.anki) setAnkiChip(state.anki);
  } catch (error) {
    view.innerHTML = `<div class="empty" style="margin-top:40px"><strong>加载失败</strong>${esc(error.message)}<div style="margin-top:14px"><button class="ghost-btn" onclick="location.reload()">重试</button></div></div>`;
  }
}

function bindDynamic() {
  document.querySelectorAll("[data-go]").forEach((el) => {
    el.onclick = () => setRoute(el.dataset.go);
  });
  document.querySelectorAll("[data-action]").forEach((el) => {
    if (el.dataset.action === "open-url") return;
    el.onclick = (event) => {
      event.stopPropagation();
      handleAction(el.dataset.action, el);
    };
  });
}

async function handleAction(action, el) {
  if (action === "anki-launch") {
    if (state.route === "vocab") return runAnkiAction("launch");
    try {
      await api("/api/anki/launch", { method: "POST" });
      toast("Anki 已启动", "ok");
      refreshAnkiChip();
    } catch (error) { toast(error.message, "bad"); }
  } else if (action === "anki-setup") {
    runAnkiAction("setup");
  } else if (action === "anki-export") {
    runAnkiAction("export");
  } else if (action === "anki-export-all") {
    runAnkiAction("export-all");
  } else if (action === "anki-refresh") {
    await loadVocab(); renderVocab(); bindDynamic();
  } else if (action === "library-refresh") {
    try {
      const data = await api("/api/library/refresh", { method: "POST" });
      toast(`Zotero 快照已刷新 · ${data.items} 条`, "ok");
      const list = await api("/api/library?limit=100");
      state.library.items = list.items;
      renderLibraryRows();
    } catch (error) { toast(error.message, "bad"); }
  } else if (action === "open-pdf") {
    try {
      await api("/api/reveal", { method: "POST", body: JSON.stringify({ path: el.dataset.path }) });
      toast("已在资源管理器中定位 PDF", "ok");
    } catch (error) { toast(error.message, "bad"); }
  } else if (action === "open-zotero") {
    try {
      await api("/api/open-url", { method: "POST", body: JSON.stringify({ url: `zotero://select/library/items/${el.dataset.key}` }) });
    } catch (error) { toast(error.message, "bad"); }
  } else if (action === "copy-cite") {
    const item = state.library.detail;
    if (!item) return;
    const cite = `${item.authors.join(", ")} (${item.year}). ${item.title}. ${item.publication}${item.doi ? `, https://doi.org/${item.doi}` : ""}`;
    try {
      await navigator.clipboard.writeText(cite);
      toast("引用已复制", "ok");
    } catch (_) { toast(cite); }
  } else if (action === "make-script") {
    const detail = state.library.detail;
    if (detail) makeScript(detail);
  } else if (action === "open-folder") {
    try {
      await api("/api/open", { method: "POST", body: JSON.stringify({ kind: el.dataset.kind }) });
    } catch (error) { toast(error.message, "bad"); }
  }
}

document.addEventListener("click", (event) => {
  const paper = event.target.closest("[data-paper]");
  if (paper) {
    const id = Number(paper.dataset.paper);
    if (state.route !== "library") {
      state.library.selected = id;
      setRoute("library");
    } else {
      openPaper(id, true);
    }
    return;
  }
  const urlLink = event.target.closest("[data-action='open-url']");
  if (urlLink) {
    event.preventDefault();
    api("/api/open-url", { method: "POST", body: JSON.stringify({ url: urlLink.dataset.url }) })
      .catch((error) => toast(error.message, "bad"));
  }
});

/* --------------------------------------------------------------- palette */

const PALETTE_ITEMS = [
  { label: "Overview", hint: "workspace", icon: "grid", run: () => setRoute("overview") },
  { label: "Library", hint: "Zotero", icon: "library", run: () => setRoute("library") },
  { label: "Speak", hint: "practice", icon: "mic", run: () => setRoute("speak") },
  { label: "Write", hint: "phrasebank", icon: "pen", run: () => setRoute("write") },
  { label: "Vocab", hint: "Anki", icon: "cards", run: () => setRoute("vocab") },
  { label: "Settings", hint: "paths", icon: "sliders", run: () => setRoute("settings") },
  { label: "Toggle light / dark", hint: "theme", icon: "sun", run: () => toggleTheme() },
  { label: "Generate sample audio", hint: "Kokoro", icon: "speaker", run: () => { setRoute("speak"); setTimeout(() => document.getElementById("tts-btn")?.click(), 500); } },
  { label: "Launch Anki", hint: "AnkiConnect", icon: "play", run: () => handleAction("anki-launch", {}) },
  { label: "Export annotations", hint: "Anki", icon: "download", run: () => { setRoute("vocab"); setTimeout(() => runAnkiAction("export"), 600); } },
  { label: "Analyze a recording", hint: "Whisper + Praat", icon: "wave", run: () => { setRoute("speak"); state.speakTab = "analyze"; setTimeout(() => renderSpeakSide(), 500); } },
  { label: "Open data folder", hint: "local", icon: "folder", run: () => api("/api/open", { method: "POST", body: JSON.stringify({ kind: "data" }) }) }
];

function openPalette() {
  const el = document.getElementById("palette");
  el.hidden = false;
  state.paletteIndex = 0;
  const input = document.getElementById("palette-input");
  input.value = "";
  renderPalette("");
  setTimeout(() => input.focus(), 30);
}

function closePalette() {
  document.getElementById("palette").hidden = true;
}

function renderPalette(query) {
  const q = query.toLowerCase();
  const items = PALETTE_ITEMS.filter((item) => !q || item.label.toLowerCase().includes(q) || item.hint.toLowerCase().includes(q));
  if (state.paletteIndex >= items.length) state.paletteIndex = 0;
  document.getElementById("palette-list").innerHTML = items.map((item, index) => `
    <div class="palette-item ${index === state.paletteIndex ? "active" : ""}" data-index="${index}">
      <span class="ico">${icon(item.icon)}</span><span>${esc(item.label)}</span><small>${esc(item.hint)}</small>
    </div>`).join("") || `<div class="empty" style="border:0">没有匹配的动作</div>`;
  document.querySelectorAll(".palette-item").forEach((el) => {
    el.onclick = () => {
      const item = items[Number(el.dataset.index)];
      closePalette();
      item.run();
    };
  });
  state.paletteItems = items;
}

function initPalette() {
  const input = document.getElementById("palette-input");
  input.addEventListener("input", () => { state.paletteIndex = 0; renderPalette(input.value); });
  input.addEventListener("keydown", (event) => {
    const items = state.paletteItems || [];
    if (event.key === "ArrowDown") { event.preventDefault(); state.paletteIndex = Math.min(items.length - 1, state.paletteIndex + 1); renderPalette(input.value); }
    if (event.key === "ArrowUp") { event.preventDefault(); state.paletteIndex = Math.max(0, state.paletteIndex - 1); renderPalette(input.value); }
    if (event.key === "Enter" && items[state.paletteIndex]) { closePalette(); items[state.paletteIndex].run(); }
  });
  document.getElementById("palette").addEventListener("click", (event) => {
    if (event.target.id === "palette") closePalette();
  });
}

/* --------------------------------------------------------------- boot */

document.getElementById("open-palette").onclick = openPalette;
document.getElementById("today-action").onclick = () => setRoute("speak");
document.getElementById("anki-chip").onclick = () => setRoute("vocab");
document.getElementById("theme-toggle").onclick = toggleTheme;
document.getElementById("brand")?.addEventListener("click", () => setRoute("overview"));
document.querySelector(".brand").onclick = () => setRoute("overview");

window.addEventListener("pywebviewready", () => {
  if (window.pywebview?.api?.set_theme) window.pywebview.api.set_theme(currentTheme());
});

document.addEventListener("keydown", (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") { event.preventDefault(); openPalette(); }
  if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key.toLowerCase() === "l") { event.preventDefault(); toggleTheme(); }
  if ((event.ctrlKey || event.metaKey) && event.key === "Enter") { event.preventDefault(); setRoute("speak"); }
  if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key.toLowerCase() === "a") { event.preventDefault(); handleAction("anki-launch", {}); }
  if (event.key === "Escape") closePalette();
});

window.addEventListener("hashchange", route);

(async function boot() {
  const forced = new URLSearchParams(location.search).get("theme");
  applyTheme(forced === "light" || forced === "dark" ? forced : currentTheme());
  initPalette();
  mountIcons(document);
  await refreshAnkiChip();
  await route();
})();
