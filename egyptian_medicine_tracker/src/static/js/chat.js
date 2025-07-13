// Floating chat widget logic

// Create chat button
const chatBtn = document.createElement('button');
chatBtn.id = 'crew-chat-btn';
chatBtn.innerHTML = '💬';
document.body.appendChild(chatBtn);

// Create chat window
const chatWindow = document.createElement('div');
chatWindow.id = 'crew-chat-window';
chatWindow.classList.add('hidden');
chatWindow.innerHTML = `
  <div id="crew-chat-header">Ask Harby Pharmacy <span id="crew-chat-close">&times;</span></div>
  <div id="crew-chat-messages"></div>
  <form id="crew-chat-form">
    <input id="crew-chat-input" type="text" placeholder="Ask a question..." autocomplete="off" />
    <button type="submit">Send</button>
  </form>
`;
document.body.appendChild(chatWindow);

// Show/hide chat window
chatBtn.onclick = () => chatWindow.classList.toggle('hidden');
document.getElementById('crew-chat-close').onclick = () => chatWindow.classList.add('hidden');

// Drag functionality
let isDragging = false, offsetX, offsetY;
chatWindow.onmousedown = function (e) {
    if (e.target.id !== 'crew-chat-header') return;
    isDragging = true;
    offsetX = e.clientX - chatWindow.offsetLeft;
    offsetY = e.clientY - chatWindow.offsetTop;
    document.onmousemove = function (e) {
        if (!isDragging) return;
        chatWindow.style.left = (e.clientX - offsetX) + 'px';
        chatWindow.style.top = (e.clientY - offsetY) + 'px';
    };
    document.onmouseup = function () { isDragging = false; document.onmousemove = null; };
};

// Generate or get a persistent user ID (per browser)
function getUserId() {
    let uid = localStorage.getItem('crew_user_id');
    if (!uid) {
        uid = 'u' + Math.random().toString(36).slice(2, 12);
        localStorage.setItem('crew_user_id', uid);
    }
    return uid;
}

// Send chat message
document.getElementById('crew-chat-form').onsubmit = async function (e) {
    e.preventDefault();
    const input = document.getElementById('crew-chat-input');
    const msg = input.value.trim();
    if (!msg) return;
    appendMessage('user', msg);
    input.value = '';
    appendMessage('bot', '<span class="crew-typing">...</span>');
    const res = await sendChat(msg);
    document.querySelector('#crew-chat-messages .crew-typing').parentNode.remove();
    appendMessage('bot', res);
};

// Append message to chat
function appendMessage(sender, text) {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'crew-chat-msg ' + sender;
    // Replace newlines with <br> for display
    msgDiv.innerHTML = text.replace(/\n/g, '<br>');
    document.getElementById('crew-chat-messages').appendChild(msgDiv);
    document.getElementById('crew-chat-messages').scrollTop = 99999;
}

// Send chat to backend
async function sendChat(message) {
    try {
        const resp = await fetch('/api/medicines/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: message, user_id: getUserId() })
        });
        const data = await resp.json();
        console.log('[Chat API reply]', data); // Debug log
        return data.reply || "Sorry, no reply.";
    } catch (e) {
        return "Error contacting server.";
    }
} 