const API = "/api";
const state = { session: "", conversation: "", lastMessage: "", timer: null, refreshing: false, sending: false, messageRefs: new Set() };
const $ = (id) => document.getElementById(id);

function setStatus(message, error = false) {
  const box = $("status");
  box.textContent = message;
  box.classList.toggle("error", error);
}

function pathTarget() {
  const parts = window.location.pathname.split("/").filter(Boolean);
  if (parts[0] !== "f") throw new Error("This finder link is incomplete.");
  if (!parts[1]) return null;
  if (parts[1] === "code" && parts[2]) {
    return { endpoint: `/f/code/${encodeURIComponent(parts[2])}`, direct: false };
  }
  return { endpoint: `/f/${encodeURIComponent(parts[1])}`, direct: true };
}

async function json(url, options = {}) {
  const response = await fetch(`${API}${url}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.error || "Something went wrong.");
  return body;
}

function addMessage(message) {
  if (state.messageRefs.has(message.message_ref)) return;
  state.messageRefs.add(message.message_ref);
  const li = document.createElement("li");
  const sender = document.createElement("strong");
  sender.textContent = message.sender_role === "finder" ? "You" : "Owner";
  const body = document.createElement("span");
  body.textContent = message.body;
  li.append(sender, body);
  $("messages").append(li);
}

async function refreshMessages() {
  if (!state.conversation || state.refreshing) return;
  state.refreshing = true;
  try {
    const body = await json(`/finder/conversations/${encodeURIComponent(state.conversation)}/messages?after=${encodeURIComponent(state.lastMessage)}`, {
      headers: { "X-Finder-Session": state.session },
    });
    for (const message of body.messages) {
      addMessage(message);
      state.lastMessage = message.created_at;
    }
  } finally {
    state.refreshing = false;
  }
}
function bindChat() {
  if ($("message-form").dataset.bound) return;
  $("message-form").dataset.bound = "true";
  $("message-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    if (state.sending || !state.conversation) return;
    const input = $("message");
    const button = event.submitter || $("message-form").querySelector("button");
    if (!input.value.trim()) return;
    state.sending = true;
    button.disabled = true;
    try {
      const message = await json(`/finder/conversations/${encodeURIComponent(state.conversation)}/messages`, {
        method: "POST",
        headers: { "X-Finder-Session": state.session },
        body: JSON.stringify({ body: input.value }),
      });
      input.value = "";
      addMessage(message);
      state.lastMessage = message.created_at;
    } catch (error) {
      setStatus(error.message, true);
    } finally {
      state.sending = false;
      button.disabled = false;
    }
  });
}

async function openConversation(report) {
  state.conversation = report.conversation_ref;
  $("report").classList.add("hidden");
  $("chat").classList.remove("hidden");
  setStatus("You are connected. Tell the owner where the item is.");
  bindChat();
  await refreshMessages();
  if (!state.timer) state.timer = window.setInterval(() => refreshMessages().catch(() => {}), 2500);
}

async function reportFound(place, note = "", authorityOrganization = "") {
  const report = await json(`/f/sessions/${encodeURIComponent(state.session)}/found`, {
    method: "POST",
    body: JSON.stringify({ place, note, authority_organization: authorityOrganization }),
  });
  sessionStorage.setItem(`bwm:found:${window.location.pathname}`, JSON.stringify(report));
  await openConversation(report);
}

async function start() {
  try {
    const target = pathTarget();
    if (!target) {
      $("code-entry").classList.remove("hidden");
      setStatus("Enter the short code printed on the label.");
      $("code-form").addEventListener("submit", (event) => {
        event.preventDefault();
        const code = $("human-code").value.trim().toUpperCase();
        window.location.assign(`/f/code/${encodeURIComponent(code)}`);
      });
      return;
    }
    const existing = sessionStorage.getItem(`bwm:${target.endpoint}`);
    const opened = existing ? JSON.parse(existing) : await json(target.endpoint);
    sessionStorage.setItem(`bwm:${target.endpoint}`, JSON.stringify(opened));
    state.session = opened.session_token;
    $("item-label").textContent = opened.label || "Found item";

    if (target.direct) {
      const previousReport = sessionStorage.getItem(`bwm:found:${window.location.pathname}`);
      if (previousReport) {
        await openConversation(JSON.parse(previousReport));
      } else {
        await reportFound("Still with me");
      }
      return;
    }

    $("report").classList.remove("hidden");
    setStatus("Add the location, then you will go straight to private chat.");
    $("authority").addEventListener("change", () => {
      $("organization").classList.toggle("hidden", !$("authority").checked);
      $("organization").required = $("authority").checked;
    });
    $("report-form").addEventListener("submit", async (event) => {
      event.preventDefault();
      try {
        await reportFound(
          $("place").value,
          $("note").value,
          $("authority").checked ? $("organization").value : "",
        );
      } catch (error) {
        setStatus(error.message, true);
      }
    });
  } catch (error) {
    setStatus(error.message, true);
  }
}

start();
