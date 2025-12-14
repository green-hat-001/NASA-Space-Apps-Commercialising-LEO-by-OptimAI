const socket = io();
const chatContainer = document.getElementById('chat-container');
const messageInput = document.getElementById('message-input');
const fileInput = document.getElementById('file-input');
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

    if (!isMine) {
        const senderDiv = document.createElement('div');
        senderDiv.className = 'sender-name';
        senderDiv.textContent = data.sender.split('@')[0];
        msgDiv.appendChild(senderDiv);
    }

    // Handle Content (Text or Image)
    if (data.type === 'image') {
        if (data.content) {
            const textDiv = document.createElement('div');
            textDiv.textContent = data.content;
            msgDiv.appendChild(textDiv);
        }
        const img = document.createElement('img');
        img.src = data.media_path;
        msgDiv.appendChild(img);
    } else {
        const textNode = document.createTextNode(data.content);
        msgDiv.appendChild(textNode);
    }

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
        socket.emit('message', { msg: content, type: 'text' });
        messageInput.value = '';
    }
    suggestionsBox.style.display = 'none';
}

function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.url) {
            // Send message with image URL
            socket.emit('message', {
                msg: messageInput.value.trim(), // Optional caption
                type: 'image',
                media_path: data.url
            });
            messageInput.value = ''; // Clear caption if sent
        } else {
            alert('Upload failed');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Upload failed');
    });
}

// File Input Change
if (fileInput) {
    fileInput.addEventListener('change', function() {
        if (this.files && this.files[0]) {
            uploadFile(this.files[0]);
            this.value = ''; // Reset
        }
    });
}

// Paste Handler
if (messageInput) {
    messageInput.addEventListener('paste', function(e) {
        const items = (e.clipboardData || e.originalEvent.clipboardData).items;
        for (let index in items) {
            const item = items[index];
            if (item.kind === 'file' && item.type.startsWith('image/')) {
                const blob = item.getAsFile();
                uploadFile(blob);
                e.preventDefault(); // Prevent pasting filename text
            }
        }
    });

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
