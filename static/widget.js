(() => {
  const panel = document.getElementById("chat-panel");
  const launcher = document.getElementById("chat-launcher");
  const closer = document.getElementById("chat-close");
  const log = document.getElementById("chat-log");
  const form = document.getElementById("chat-form");
  const input = document.getElementById("chat-input");

  const sessionId =
    localStorage.getItem("webchat_session") ||
    (() => {
      const id = "sess_" + Math.random().toString(36).slice(2, 10);
      localStorage.setItem("webchat_session", id);
      return id;
    })();

  function addBubble(text, who) {
    const el = document.createElement("div");
    el.className = "bubble " + who;
    el.textContent = text;
    log.appendChild(el);
    log.scrollTop = log.scrollHeight;
  }

  launcher.addEventListener("click", () => {
    panel.classList.add("open");
    if (!log.dataset.booted) {
      addBubble(
        "Hi — I can answer quick questions or take a project request.\nType lead to start, or ask about pricing / WhatsApp / Slack / Zapier.",
        "bot"
      );
      log.dataset.booted = "1";
    }
    input.focus();
  });

  closer.addEventListener("click", () => panel.classList.remove("open"));

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = input.value.trim();
    if (!message) return;
    addBubble(message, "user");
    input.value = "";
    input.disabled = true;

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, message }),
      });
      if (!response.ok) {
        addBubble("Server error " + response.status + ". Is uvicorn running?", "bot");
        return;
      }
      const payload = await response.json();
      for (const reply of payload.replies || []) {
        addBubble(reply, "bot");
      }
    } catch (err) {
      addBubble("Could not reach API. Start: uvicorn main:app --port 8790", "bot");
    } finally {
      input.disabled = false;
      input.focus();
    }
  });
})();
