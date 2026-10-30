// Prism 划词的后台：所有对本地服务的请求都从这里走，
// Prism 没开时先把条目排进 chrome.storage，等它回来再补交。

const BASE = "http://127.0.0.1:7317";
const OUTBOX = "outbox";
const FLUSH_MS = 60000;

async function request(path, options = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 2500);
  try {
    const response = await fetch(BASE + path, {
      method: options.method || "GET",
      headers: options.body ? { "Content-Type": "application/json" } : undefined,
      body: options.body ? JSON.stringify(options.body) : undefined,
      credentials: "omit",
      signal: controller.signal,
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
  } finally {
    clearTimeout(timer);
  }
}

async function getOutbox() {
  const stored = await chrome.storage.local.get(OUTBOX);
  return Array.isArray(stored[OUTBOX]) ? stored[OUTBOX] : [];
}

async function setOutbox(rows) {
  await chrome.storage.local.set({ [OUTBOX]: rows.slice(-200) });
}

async function queue(clip) {
  const rows = await getOutbox();
  rows.push({ ...clip, queued: Date.now() });
  await setOutbox(rows);
  return rows.length;
}

async function flush() {
  const rows = await getOutbox();
  if (!rows.length) return 0;
  const left = [];
  let sent = 0;
  for (const row of rows) {
    try {
      await request("/api/clips", { method: "POST", body: row.clip || row });
      sent += 1;
    } catch (_) {
      left.push(row);
    }
  }
  await setOutbox(left);
  return sent;
}

async function refreshBadge() {
  let label = "";
  try {
    const status = await request("/api/clips?limit=1");
    const queued = (await getOutbox()).length;
    const total = (status.pending || 0) + queued;
    label = total ? String(Math.min(total, 999)) : "";
  } catch (_) {
    const queued = (await getOutbox()).length;
    label = queued ? `+${queued}` : "!";
  }
  await chrome.action.setBadgeText({ text: label });
  await chrome.action.setBadgeBackgroundColor({ color: "#b85c4a" });
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  (async () => {
    try {
      if (message.type === "lookup") {
        sendResponse({ ok: true, data: await request(`/api/dict?q=${encodeURIComponent(message.text)}`) });
      } else if (message.type === "clip") {
        try {
          const data = await request("/api/clips", { method: "POST", body: message.payload });
          sendResponse({ ok: true, data, stored: true });
        } catch (error) {
          const size = await queue(message.payload);
          sendResponse({ ok: true, queued: size, stored: false, reason: String(error.message || error) });
        }
      } else if (message.type === "status") {
        const queued = await getOutbox();
        try {
          const data = await request("/api/clips?limit=1");
          sendResponse({ ok: true, online: true, queued: queued.length, data });
        } catch (error) {
          sendResponse({ ok: true, online: false, queued: queued.length, reason: String(error.message || error) });
        }
      } else if (message.type === "flush") {
        sendResponse({ ok: true, sent: await flush() });
      } else {
        sendResponse({ ok: false, reason: "unknown message" });
      }
    } catch (error) {
      sendResponse({ ok: false, reason: String(error.message || error) });
    }
  })();
  return true;
});

chrome.runtime.onInstalled.addListener(() => {
  chrome.alarms.create("prism-flush", { periodInMinutes: FLUSH_MS / 60000 });
  refreshBadge();
});

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name !== "prism-flush") return;
  flush().then(refreshBadge);
});

refreshBadge();
