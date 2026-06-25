let currentSessionId = null; 
let isFirstChatInSession = true;

document.addEventListener("DOMContentLoaded", () => {
    loadSessions();

    // Kontrol Manual Sidebar via Tombol ☰
    document.getElementById('menuBtn').addEventListener('click', () => {
        document.getElementById('sidebar').classList.toggle('collapsed');
    });

    // Tombol New Chat
    document.getElementById('newChatBtn').addEventListener('click', () => {
        currentSessionId = null;
        isFirstChatInSession = true;
        document.getElementById('chatContainer').innerHTML = `
            <div class="welcome-screen" id="welcomeScreen">
                <h1 class="animate-fade-up">Halo, Ian</h1>
                <p class="animate-fade-up-delay">How can I assist your tech journey today?</p>
            </div>`;
        loadSessions();
    });

    // Input keyboard event handler
    document.getElementById('userInput').addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            kirimPesan();
        }
    });

    document.getElementById('sendBtn').addEventListener('click', kirimPesan);
});

async function loadSessions() {
    try {
        const response = await fetch('/api/sessions');
        const sessions = await response.json();
        const listContainer = document.getElementById('historyList');
        listContainer.innerHTML = '';

        if (!sessions || !Array.isArray(sessions)) return;

        sessions.forEach(s => {
            const idSesi = s.session_id;
            const judulSesi = s.judul;
            if (!idSesi || !judulSesi) return;

            const item = document.createElement('div');
            item.className = `history-item ${idSesi === currentSessionId ? 'active' : ''}`;
            item.innerHTML = `
                <div class="history-title" onclick="switchSession(${idSesi})">💬 ${judulSesi}</div>
                <div class="history-actions">
                    <button class="action-btn" onclick="renameSession(${idSesi})">✏️</button>
                    <button class="action-btn" onclick="deleteSession(${idSesi})">🗑️</button>
                </div>
            `;
            listContainer.appendChild(item);
        });
    } catch (e) { console.error("Gagal memuat histori", e); }
}

async function switchSession(id) {
    currentSessionId = id;
    isFirstChatInSession = false;
    document.getElementById('sidebar').classList.add('collapsed');
    
    const response = await fetch(`/api/history?session_id=${id}`);
    const history = await response.json();
    
    const container = document.getElementById('chatContainer');
    container.innerHTML = '';
    
    if (history && Array.isArray(history)) {
        history.forEach(chat => {
            appendBubble(chat.content, chat.role === 'user');
        });
    }
    loadSessions();
}

async function renameSession(id) {
    const newName = prompt("Masukkan nama histori baru:");
    if (!newName) return;
    await fetch('/api/session/rename', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ id: id, title: newName })
    });
    loadSessions();
}

async function deleteSession(id) {
    if (!confirm("Hapus obrolan ini secara permanen?")) return;
    await fetch('/api/session/delete', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ id: id })
    });
    if(id === currentSessionId) {
        document.getElementById('newChatBtn').click();
    } else {
        loadSessions();
    }
}

function autoGrow(element) {
    element.style.height = "5px";
    element.style.height = (element.scrollHeight) + "px";
}

// ==================== FIX TOTAL PAKAI MARKED PARSER ====================
// Fungsi translator format markdown bawaan (Cukup bold dan ganti \n jadi <br>)
// Fungsi translator format markdown + custom newline placeholder
function formatMarkdownToHtml(rawText) {
    if (!rawText) return "";
    return rawText
        // Ganti placeholder aman dari Python menjadi tag enter HTML murni
        .replace(/\[NEWLINE\]/g, "<br>")
        // Ganti format bold markdown menjadi text tebal HTML
        .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
        // Berjaga-jaga jika ada enter \n asli yang lolos
        .replace(/\n/g, "<br>");
}

async function kirimPesan() {
    const input = document.getElementById('userInput');
    const text = input.value.trim();
    if (!text) return;

    const welcome = document.getElementById('welcomeScreen');
    if (welcome) welcome.classList.add('hidden');
    document.getElementById('sidebar').classList.add('collapsed');

    appendBubble(text, true);
    input.value = '';
    autoGrow(input);

    const responseRow = appendBubble('<span class="thinking-dots">Thinking...</span>', false);
    const textNode = responseRow.querySelector(".neira-text");

    const encText = encodeURIComponent(text);
    const eventSource = new EventSource(`/api/chat-stream?pesan=${encText}&session_id=${currentSessionId || ''}`);
    
    let isFirstToken = true;
    let accumulatedText = ""; // Buffer murni tanpa tambahan spasi buatan

    eventSource.onmessage = function(event) {
        // 1. Cek assignment Session ID baru
        if (event.data.startsWith("[SESSION_ID_ASSIGNED:")) {
            const extractedId = event.data.match(/\d+/)[0];
            currentSessionId = parseInt(extractedId);
            return;
        }

        // 2. Cek status Done
        if (event.data === "[DONE]") {
            eventSource.close();
            isFirstChatInSession = false;
            loadSessions(); 
            return;
        }

        // 3. PROSES DATA TOKEN CHAT
        if (isFirstToken) {
            textNode.innerHTML = "";
            isFirstToken = false;
        }
        
        let tokenMurni = "";

        try {
            // Coba parse jika formatnya JSON (kiriman dari chunk bungkusan json.dumps)
            const dataObj = JSON.parse(event.data);
            if (dataObj && dataObj.text !== undefined) {
                tokenMurni = dataObj.text;
            } else {
                tokenMurni = event.data;
            }
        } catch(e) {
            // Jika gagal di-parse (berarti string plain biasa), pakai datanya langsung
            tokenMurni = event.data;
        }

        // Masukkan token murni yang aman ke buffer utama
        accumulatedText += tokenMurni;
        
        // Render langsung menggunakan parser markdown-to-html custom kita
        textNode.innerHTML = formatMarkdownToHtml(accumulatedText);
        
        const container = document.getElementById('chatContainer');
        container.scrollTop = container.scrollHeight;
    };

    eventSource.onerror = function() {
        textNode.innerHTML = "⚠️ Error streaming data dari Neira Ecosystem.";
        eventSource.close();
    };
}

function appendBubble(text, isUser) {
    const container = document.getElementById('chatContainer');
    const row = document.createElement('div');
    row.className = isUser ? 'chat-row user-row' : 'chat-row neira-row';
    
    let processedText = isUser ? text : formatMarkdownToHtml(text);
    if (!isUser && text.includes("thinking-dots")) {
        processedText = text; 
    }

    row.innerHTML = isUser ? 
        `<div class="user-bubble">${processedText}</div>` : 
        `<div class="neira-icon">✦</div><div class="neira-text">${processedText}</div>`;
        
    container.appendChild(row);
    container.scrollTop = container.scrollHeight;
    return row;
}

// AMAN: Bagian shutdown beacon kita hapus total dari sini agar pas di-refresh Neira TIDAK MATI!

// Sinyal mati otomatis ketika tab web ditutup oleh user
window.addEventListener('beforeunload', () => {
    navigator.sendBeacon('/api/shutdown');
});