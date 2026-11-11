// Antarmuka chat InvestBot: kirim pesan dengan fetch(), tampilkan balasan tanpa reload
const messages = document.getElementById("messages");
const form = document.getElementById("chat-form");
const input = document.getElementById("chat-input");

// addMessage: tambah satu gelembung pesan (textContent = aman dari XSS)
function addMessage(sender, text, meta) {
  const row = document.createElement("div");
  row.className = `msg msg-${sender}`;
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = (sender === "bot" ? AVATAR + " " : "") + text;
  if (meta) {
    const small = document.createElement("small");
    small.textContent = meta;
    bubble.appendChild(small);
  }
  row.appendChild(bubble);
  messages.appendChild(row);
  messages.scrollTop = messages.scrollHeight;
  return row;
}

// sendMessage: kirim pesan ke /api/chat lalu tampilkan jawaban
async function sendMessage(text) {
  addMessage("user", text);
  const typing = addMessage("bot", "sedang mengetik...");
  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    });
    const data = await res.json();
    typing.remove();
    if (!res.ok) return addMessage("bot", "⚠ " + data.error);
    addMessage("bot", data.reply, `intent: ${data.intent || "tidak dikenali"} · skor ${data.score.toFixed(2)}`);
  } catch (err) {
    typing.remove();
    addMessage("bot", "⚠ Gagal terhubung ke server.");
  }
}

form.addEventListener("submit", (e) => {  // submit: cegah reload, kirim pesan
  e.preventDefault();
  const text = input.value.trim();
  if (!text) return;
  input.value = "";
  sendMessage(text);
});

document.querySelectorAll(".chip").forEach((chip) =>
  chip.addEventListener("click", () => sendMessage(chip.textContent)));

addMessage("bot", GREETING);
