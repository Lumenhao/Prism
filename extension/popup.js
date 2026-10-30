// 弹窗只做三件事：报告 Prism 是否在线、开关划词、手动补交队列。

const statusEl = document.getElementById("status");
const enabledEl = document.getElementById("enabled");
const flushEl = document.getElementById("flush");

function send(message) {
  return new Promise((resolve) => chrome.runtime.sendMessage(message, resolve));
}

function render(line, cls) {
  statusEl.textContent = line;
  statusEl.className = `status ${cls}`;
}

async function refresh() {
  const reply = await send({ type: "status" });
  if (!reply || !reply.ok) return render("后台出错了，重新加载扩展试试。", "off");
  if (!reply.online) {
    return render(
      reply.queued ? `Prism 没开 · 已排队 ${reply.queued} 条` : "Prism 没开 · 先在 E 盘双击 Prism.bat",
      "off"
    );
  }
  const pending = reply.data.pending || 0;
  const queueText = reply.queued ? ` · 扩展里还压着 ${reply.queued} 条` : "";
  render(pending ? `Prism 在线 · 收件箱有 ${pending} 条待写卡${queueText}` : `Prism 在线 · 收件箱是空的${queueText}`, pending ? "warn" : "");
}

enabledEl.addEventListener("change", async () => {
  await chrome.storage.local.set({ enabled: enabledEl.checked });
});

flushEl.addEventListener("click", async () => {
  flushEl.disabled = true;
  const reply = await send({ type: "flush" });
  flushEl.disabled = false;
  if (reply && reply.ok) render(reply.sent ? `已补交 ${reply.sent} 条。` : "没有需要补交的条目。", "status");
  refresh();
});

chrome.storage.local.get("enabled").then((stored) => {
  enabledEl.checked = stored.enabled !== false;
});
refresh();
