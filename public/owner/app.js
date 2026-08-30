let token = sessionStorage.getItem("owner_session") || "";
let selected = null;
let lastMessage = "";
let inboxTimer = null;
let messageTimer = null;
const byId = (id) => document.getElementById(id);

function status(text, error = false) {
  const element = byId("status");
  element.textContent = text;
  element.classList.toggle("error", error);
}

async function api(path, options = {}) {
  const response = await fetch(`/api${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.error || "Request failed");
  return body;
}

async function loadInbox() {
  const body = await api("/owner/inbox");
  const events = byId("events");
  events.replaceChildren();
  if (!body.events.length) {
    const empty = document.createElement("p");
    empty.className = "muted";
    empty.textContent = "No found reports yet.";
    events.append(empty);
  }
  for (const event of body.events) {
    const card = document.createElement("article");
    card.className = "card";
    const title = document.createElement("h3");
    title.textContent = event.label;
    const text = document.createElement("p");
    text.textContent = `${event.place}${event.note ? ` — ${event.note}` : ""}`;
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = "Open chat";
    button.addEventListener("click", () => openChat(event));
    card.append(title, text, button);
    events.append(card);
  }
}

async function provisionTag(item, button, result) {
  button.disabled = true;
  try {
    const tag = await api(`/items/${encodeURIComponent(item.item_ref)}/tags`, { method: "POST" });
    result.replaceChildren();
    result.className = "muted";
    result.append(`Short code: ${tag.human_code} · `);
    const link = document.createElement("a");
    link.href = tag.finder_url;
    link.target = "_blank";
    link.rel = "noreferrer";
    link.textContent = "Open finder page";
    result.append(link);
    status(`Tag ready for ${item.label}. Open the finder page in a second browser tab.`);
  } catch (error) {
    status(error.message, true);
  } finally {
    button.disabled = false;
  }
}

async function loadItems() {
  const body = await api("/items");
  const items = byId("items");
  items.replaceChildren();
  if (!body.items.length) {
    const empty = document.createElement("p");
    empty.className = "muted";
    empty.textContent = "No items yet.";
    items.append(empty);
  }
  for (const item of body.items) {
    const card = document.createElement("article");
    card.className = "card";
    const title = document.createElement("h3");
    title.textContent = item.label;
    const details = document.createElement("p");
    details.className = "muted";
    details.textContent = item.status;
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = "Provision NFC / QR tag";
    const result = document.createElement("p");
    result.className = "muted";
    button.addEventListener("click", () => void provisionTag(item, button, result));
    card.append(title, details, button, result);
    items.append(card);
  }
}

async function loadDashboard() {
  await Promise.all([loadInbox(), loadItems()]);
  byId("dashboard").classList.remove("hidden");
}

async function openChat(event) {
  selected = event;
  lastMessage = "";
  byId("chat-title").textContent = `Chat about ${event.label}`;
  byId("chat").classList.remove("hidden");
  byId("messages").replaceChildren();
  byId("call-status").textContent = "";
  if (messageTimer) window.clearInterval(messageTimer);
  await pollMessages();
  messageTimer = window.setInterval(() => pollMessages().catch((error) => status(error.message, true)), 2500);
}

async function pollMessages() {
  if (!selected) return;
  const body = await api(`/owner/conversations/${encodeURIComponent(selected.conversation_ref)}/messages?after=${encodeURIComponent(lastMessage)}`);
  for (const message of body.messages) {
    const line = document.createElement("li");
    const sender = document.createElement("strong");
    sender.textContent = message.sender_role;
    const text = document.createElement("span");
    text.textContent = message.body;
    line.append(sender, text);
    byId("messages").append(line);
    lastMessage = message.created_at;
  }
}

function startPolling() {
  if (inboxTimer) window.clearInterval(inboxTimer);
  inboxTimer = window.setInterval(() => loadInbox().catch((error) => status(error.message, true)), 5000);
}

function showLogin() {
  byId("login").classList.remove("hidden");
  byId("dashboard").classList.add("hidden");
  byId("chat").classList.add("hidden");
}

async function showDashboard() {
  byId("login").classList.add("hidden");
  await loadDashboard();
  startPolling();
  status("Owner browser fallback is ready. The native app uses the same account and API.");
}

byId("register").addEventListener("click", async () => {
  const button = byId("register");
  button.disabled = true;
  try {
    const response = await fetch("/api/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: byId("name").value, email: byId("email").value }),
    });
    const body = await response.json();
    if (!response.ok || !body.session_token) throw new Error(body.error || "Registration failed");
    token = body.session_token;
    sessionStorage.setItem("owner_session", token);
    await showDashboard();
  } catch (error) {
    status(error.message, true);
  } finally {
    button.disabled = false;
  }
});

byId("item-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = event.submitter;
  button.disabled = true;
  try {
    await api("/items", {
      method: "POST",
      body: JSON.stringify({
        label: byId("item-label").value,
        description: byId("item-description").value,
      }),
    });
    byId("item-label").value = "";
    byId("item-description").value = "";
    await loadItems();
    status("Item added. Provision a tag, then open its finder page.");
  } catch (error) {
    status(error.message, true);
  } finally {
    button.disabled = false;
  }
});

byId("message-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!selected) return;
  const input = byId("message");
  try {
    const message = await api(`/owner/conversations/${encodeURIComponent(selected.conversation_ref)}/messages`, {
      method: "POST",
      body: JSON.stringify({ body: input.value }),
    });
    input.value = "";
    lastMessage = message.created_at;
    await pollMessages();
  } catch (error) {
    status(error.message, true);
  }
});

byId("call-button").addEventListener("click", async () => {
  if (!selected) return;
  const button = byId("call-button");
  const output = byId("call-status");
  button.disabled = true;
  output.textContent = "Requesting call access…";
  try {
    const body = await api(`/owner/conversations/${encodeURIComponent(selected.conversation_ref)}/call-token`, { method: "POST" });
    output.textContent = `Call token ready for room ${body.room}. Use the native app or a LiveKit client to join.`;
  } catch (error) {
    output.textContent = error.message;
  } finally {
    button.disabled = false;
  }
});

byId("logout").addEventListener("click", () => {
  token = "";
  selected = null;
  sessionStorage.removeItem("owner_session");
  if (inboxTimer) window.clearInterval(inboxTimer);
  if (messageTimer) window.clearInterval(messageTimer);
  showLogin();
  status("Owner session closed.");
});

if (token) {
  showDashboard().catch((error) => {
    token = "";
    sessionStorage.removeItem("owner_session");
    showLogin();
    status(error.message, true);
  });
}
