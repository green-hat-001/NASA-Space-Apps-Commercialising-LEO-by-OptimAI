const socket = io();
const chatContainer = document.getElementById('chat-container');
const messageInput = document.getElementById('message-input');
const fileInput = document.getElementById('file-input');
const suggestionsBox = document.getElementById('emoji-suggestions');
const previewArea = document.getElementById('preview-area');
const sendBtn = document.getElementById('send-btn');

let pendingFile = null;

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
        img.onclick = function() { openLightbox(this.src); }; // Add click handler
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

function handleFileSelect(file) {
    if (!file || !file.type.startsWith('image/')) return;

    pendingFile = file;

    // Read and preview
    const reader = new FileReader();
    reader.onload = function(e) {
        previewArea.innerHTML = `
            <div class="preview-item">
                <img src="${e.target.result}">
                <button class="preview-remove" onclick="clearPreview()">&times;</button>
            </div>
        `;
        previewArea.style.display = 'block';
    };
    reader.readAsDataURL(file);
}

function clearPreview() {
    pendingFile = null;
    previewArea.innerHTML = '';
    previewArea.style.display = 'none';
}

function sendMessage() {
    const content = messageInput.value.trim();

    if (pendingFile) {
        // Disable button
        sendBtn.disabled = true;
        sendBtn.classList.add('loading');
        sendBtn.textContent = '...';

        const formData = new FormData();
        formData.append('file', pendingFile);

        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.url) {
                socket.emit('message', {
                    msg: content,
                    type: 'image',
                    media_path: data.url
                });
                messageInput.value = '';
                clearPreview();
            } else {
                alert('Upload failed');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Upload failed');
        })
        .finally(() => {
            sendBtn.disabled = false;
            sendBtn.classList.remove('loading');
            sendBtn.textContent = 'Send';
        });

    } else if (content) {
        socket.emit('message', { msg: content, type: 'text' });
        messageInput.value = '';
    }

    suggestionsBox.style.display = 'none';
}

// File Input Change
if (fileInput) {
    fileInput.addEventListener('change', function() {
        if (this.files && this.files[0]) {
            handleFileSelect(this.files[0]);
            this.value = ''; // Reset input so same file can be selected again if needed
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
                handleFileSelect(blob);
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

// Global Lightbox Logic
window.openLightbox = function(url) {
    const lightbox = document.getElementById('lightbox');
    const img = document.getElementById('lightbox-img');
    img.src = url;
    lightbox.classList.add('active');
};

window.closeLightbox = function() {
    document.getElementById('lightbox').classList.remove('active');
};

// Panic Key Logic
if (typeof panicKeyConfig !== 'undefined' && panicKeyConfig) {
    document.addEventListener('keydown', function(e) {
        // Only trigger if lightbox is NOT open?
        // Actually fine if it triggers anywhere.

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
