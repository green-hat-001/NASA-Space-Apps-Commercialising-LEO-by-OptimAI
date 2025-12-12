const socket = io();
const chatContainer = document.getElementById('chat-container');
const messageInput = document.getElementById('message-input');
const suggestionsBox = document.getElementById('emoji-suggestions');

// Auto-scroll logic
function scrollToBottom(force = false) {
    const isAtBottom = chatContainer.scrollHeight - chatContainer.scrollTop <= chatContainer.clientHeight + 100;
    if (force || isAtBottom) {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
}

// Initial scroll
scrollToBottom(true);

socket.on('message', function(data) {
    const msgDiv = document.createElement('div');
    const isMine = data.sender === currentUserEmail;

    msgDiv.className = `message ${isMine ? 'mine' : 'theirs'}`;

    let senderHtml = '';
    if (!isMine) {
        const senderName = data.sender.split('@')[0];
        senderHtml = `<div class="sender-name">${senderName}</div>`;
    }

    msgDiv.innerHTML = `
        ${senderHtml}
        ${data.content}
        <div class="meta">
            <span>${data.timestamp}</span>
        </div>
    `;

    chatContainer.appendChild(msgDiv);
    scrollToBottom();
});

function sendMessage() {
    const content = messageInput.value.trim();
    if (content) {
        socket.emit('message', { msg: content });
        messageInput.value = '';
    }
    suggestionsBox.style.display = 'none';
}

messageInput.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

// Emoji Autocomplete
const emojis = {
    'fire': '🔥',
    'smile': '🙂',
    'heart': '❤️',
    'thumb': '👍',
    'laugh': '😂',
    'cry': '😭',
    'wink': '😉',
    'rocket': '🚀',
    'eyes': '👀',
    'skull': '💀'
};

messageInput.addEventListener('input', function() {
    const val = this.value;
    const match = val.match(/:([a-z]*)$/);

    if (match) {
        const query = match[1];
        const suggestions = Object.keys(emojis).filter(name => name.startsWith(query));

        if (suggestions.length > 0) {
            suggestionsBox.innerHTML = suggestions.map(name =>
                `<div class="emoji-item" onclick="insertEmoji('${emojis[name]}', '${match[0]}')">
                    <span>:${name}</span> <span>${emojis[name]}</span>
                </div>`
            ).join('');
            suggestionsBox.style.display = 'block';
        } else {
            suggestionsBox.style.display = 'none';
        }
    } else {
        suggestionsBox.style.display = 'none';
    }
});

window.insertEmoji = function(emoji, trigger) {
    const text = messageInput.value;
    // Replace the last occurrence of the trigger
    const newText = text.slice(0, text.lastIndexOf(trigger)) + emoji + ' ';
    messageInput.value = newText;
    suggestionsBox.style.display = 'none';
    messageInput.focus();
};
