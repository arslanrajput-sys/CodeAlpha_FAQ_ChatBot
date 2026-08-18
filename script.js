const form = document.getElementById("chatForm");
const input = document.getElementById("questionInput");
const sendButton = document.getElementById("sendButton");
const messages = document.getElementById("chatMessages");
const clearChat = document.getElementById("clearChat");

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

function quickQuestionsMarkup() {
  return `
    <div class="quick-section" id="quickQuestions">
      <span>Popular questions</span>
      <div class="quick-list">
        <button type="button" data-question="I forgot my online banking password. What should I do?">Reset my password</button>
        <button type="button" data-question="What should I do if my debit card is lost or stolen?">Lost or stolen card</button>
        <button type="button" data-question="What is the daily ATM withdrawal limit?">ATM withdrawal limit</button>
        <button type="button" data-question="How long does an external bank transfer take?">Transfer timing</button>
      </div>
    </div>
  `;
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
  if (data.source === "grounded-knowledge" && data.matched_question) {
    matchInfo = `
      <span class="match-note">
        Related help topic: ${escapeHTML(data.matched_question)}
      </span>
    `;
  }

  row.innerHTML = `
    <div class="avatar">S</div>
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
    <div class="avatar">S</div>
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

  document.getElementById("quickQuestions")?.remove();

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

messages.addEventListener("click", (event) => {
  const button = event.target.closest("[data-question]");
  if (!button) return;
  askQuestion(button.dataset.question || "");
});

clearChat.addEventListener("click", () => {
  messages.innerHTML = `
    <div class="message-row bot">
      <div class="avatar">S</div>
      <div class="message-content">
        <div class="message-bubble">Welcome. What can we help you with today?</div>
        <span class="message-meta">SecureBank support</span>
      </div>
    </div>
    ${quickQuestionsMarkup()}
  `;
  input.value = "";
  autoResize();
  input.focus();
});

input.focus();
