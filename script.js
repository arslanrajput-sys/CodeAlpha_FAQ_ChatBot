const form = document.getElementById("chatForm");
const input = document.getElementById("questionInput");
const sendButton = document.getElementById("sendButton");
const messages = document.getElementById("chatMessages");
const clearChat = document.getElementById("clearChat");
const quickQuestions = document.getElementById("quickQuestions");

function escapeHTML(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function scrollToBottom() {
  messages.scrollTop = messages.scrollHeight;
}

function autoResize() {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 140)}px`;
}

function addUserMessage(text) {
  const row = document.createElement("div");
  row.className = "message-row user";
  row.innerHTML = `
    <div class="message-content">
      <div class="message-bubble">${escapeHTML(text)}</div>
      <span class="message-meta">You</span>
    </div>
  `;
  messages.appendChild(row);
  scrollToBottom();
}

function addBotMessage(answer, data = {}) {
  const row = document.createElement("div");
  row.className = "message-row bot";

  let matchInfo = "";
  if (data.matched && data.matched_question) {
    matchInfo = `
      <span class="match-note">
        Related help topic: ${escapeHTML(data.matched_question)}
      </span>
    `;
  }

  row.innerHTML = `
    <div class="avatar">SB</div>
    <div class="message-content">
      <div class="message-bubble">${escapeHTML(answer)}</div>
      ${matchInfo}
      <span class="message-meta">SecureBank support</span>
    </div>
  `;

  messages.appendChild(row);
  scrollToBottom();
}

function showTyping() {
  const row = document.createElement("div");
  row.className = "message-row bot";
  row.id = "typingIndicator";
  row.innerHTML = `
    <div class="avatar">SB</div>
    <div class="message-content">
      <div class="message-bubble typing-dots" aria-label="Assistant is thinking">
        <span></span><span></span><span></span>
      </div>
    </div>
  `;
  messages.appendChild(row);
  scrollToBottom();
}

function hideTyping() {
  document.getElementById("typingIndicator")?.remove();
}

async function askQuestion(question) {
  const cleanQuestion = question.trim();
  if (!cleanQuestion || sendButton.disabled) return;

  if (quickQuestions) {
    quickQuestions.style.display = "none";
  }

  addUserMessage(cleanQuestion);
  input.value = "";
  autoResize();

  sendButton.disabled = true;
  showTyping();

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ question: cleanQuestion })
    });

    const data = await response.json();
    hideTyping();

    if (!response.ok) {
      throw new Error(data.error || "Request failed.");
    }

    addBotMessage(data.answer, data);
  } catch (error) {
    hideTyping();
    addBotMessage(
      "I couldn't reach the support service right now. Please try again in a moment."
    );
    console.error(error);
  } finally {
    sendButton.disabled = false;
    input.focus();
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  askQuestion(input.value);
});

input.addEventListener("input", autoResize);

input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

document.querySelectorAll("[data-question]").forEach((button) => {
  button.addEventListener("click", () => {
    askQuestion(button.dataset.question);
  });
});

clearChat.addEventListener("click", () => {
  messages.innerHTML = `
    <div class="message-row bot">
      <div class="avatar">SB</div>
      <div class="message-content">
        <div class="message-bubble">
          Welcome back. What can we help you with?
        </div>
        <span class="message-meta">SecureBank support</span>
      </div>
    </div>
  `;
  input.value = "";
  autoResize();
  input.focus();
});

input.focus();
