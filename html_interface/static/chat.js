const socket = io();
const chatContainer = document.getElementById('chat-container');
const messageInput = document.getElementById('message-input');
const suggestionsBox = document.getElementById('emoji-suggestions');

// Auto-scroll logic
function scrollToBottom(force = false) {
    if (!chatContainer) return;
    const isAtBottom = chatContainer.scrollHeight - chatContainer.scrollTop <= chatContainer.clientHeight + 100;
    if (force || isAtBottom) {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
}

// Initial scroll
scrollToBottom(true);

socket.on('message', function(data) {
    if (!chatContainer) return;
    const msgDiv = document.createElement('div');
    const isMine = data.sender === currentUserEmail;

    msgDiv.className = `message ${isMine ? 'mine' : 'theirs'}`;

    // Create elements individually to prevent XSS
    if (!isMine) {
        const senderDiv = document.createElement('div');
        senderDiv.className = 'sender-name';
        senderDiv.textContent = data.sender.split('@')[0];
        msgDiv.appendChild(senderDiv);
    }

    // Add text content safely
    // Note: We are appending a text node directly to the msgDiv (or checking for mixed content)
    // The previous implementation used innerHTML with ${data.content}.
    // Here we want the text to appear after the sender name (if present).
    const textNode = document.createTextNode(data.content);
    msgDiv.appendChild(textNode);

    // Meta (timestamp)
    const metaDiv = document.createElement('div');
    metaDiv.className = 'meta';
    const span = document.createElement('span');
    span.textContent = data.timestamp;
    metaDiv.appendChild(span);
    msgDiv.appendChild(metaDiv);

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

if (messageInput) {
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    // Emoji Autocomplete logic ...
    const emojis = {
        'fire': '🔥', 'smile': '🙂', 'heart': '❤️', 'thumb': '👍',
        'laugh': '😂', 'cry': '😭', 'wink': '😉', 'rocket': '🚀',
        'eyes': '👀', 'skull': '💀'
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
}

window.insertEmoji = function(emoji, trigger) {
    const text = messageInput.value;
    const newText = text.slice(0, text.lastIndexOf(trigger)) + emoji + ' ';
    messageInput.value = newText;
    suggestionsBox.style.display = 'none';
    messageInput.focus();
};

// Panic Key Logic
if (typeof panicKeyConfig !== 'undefined' && panicKeyConfig) {
    document.addEventListener('keydown', function(e) {
        let keys = [];
        if (e.ctrlKey) keys.push('Ctrl');
        if (e.altKey) keys.push('Alt');
        if (e.shiftKey) keys.push('Shift');
        if (e.metaKey) keys.push('Meta');

        if (!['Control', 'Alt', 'Shift', 'Meta'].includes(e.key)) {
            keys.push(e.key.toUpperCase());
        }

        const combo = keys.join('+');
        if (combo === panicKeyConfig) {
            window.location.href = decoyUrl;
        }
    });
}
