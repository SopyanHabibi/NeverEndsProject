// js/chat.js
import { autoGrow, formatMarkdownToHtml } from './ui.js';
import { currentSessionId, loadSessions, setSessionId, setIsFirstChat } from './session.js';

// BARU: retry highlight kalau Prism belum ke-load pas [DONE] diterima,
// biar gak diem-diem skip & warna hilang permanen kayak sebelumnya.
function highlightCodeDenganRetry(textNode, percobaanKe = 0) {
    const MAKS_PERCOBAAN = 10;
    const JEDA_MS = 300;

    if (window.Prism) {
        textNode.querySelectorAll('code[class*="language-"]').forEach(el => {
            Prism.highlightElement(el);
        });
        return;
    }

    if (percobaanKe < MAKS_PERCOBAAN) {
        setTimeout(() => highlightCodeDenganRetry(textNode, percobaanKe + 1), JEDA_MS);
    } else {
        console.warn('Prism gagal load setelah beberapa percobaan, syntax highlight dilewati.');
    }
}

export async function kirimPesan() {
    const input = document.getElementById('userInput');
    if (!input || input.value.trim() === '') return;

    const text = input.value;

    input.value = '';
    
    // Kembalikan tinggi textarea ke baris tunggal setelah kirim pesan
    input.style.height = '24px'; 

    await kirimPesanDenganTeks(text);
}

export async function kirimPesanDenganTampilanCustom(displayHtml, actualPrompt) {
    const welcome = document.getElementById('welcomeScreen');
    if (welcome) welcome.classList.add('hidden');
    document.getElementById('sidebar').classList.add('collapsed');

    appendBubble(displayHtml, true);

    const responseRow = appendBubble('<span class="thinking-dots">...</span>', false);
    const textNode = responseRow.querySelector(".neira-text");

    const encText = encodeURIComponent(actualPrompt);
    const eventSource = new EventSource(`/api/chat-stream?pesan=${encText}&session_id=${currentSessionId || ''}`);

    let isFirstToken = true;
    let accumulatedText = "";

    eventSource.onmessage = function(event) {
        if (event.data.startsWith("[SESSION_ID_ASSIGNED:")) {
            const extractedId = event.data.match(/\d+/)[0];
            setSessionId(parseInt(extractedId));
            return;
        }

        // Deteksi sinyal minta konfirmasi tool (parse JSON envelope dulu)
        let kemungkinanTeks = "";
        try {
            const dataObjCek = JSON.parse(event.data);
            kemungkinanTeks = dataObjCek.text || "";
        } catch (e) {
            kemungkinanTeks = "";
        }

        if (kemungkinanTeks.startsWith("[TOOL_CONFIRM_REQUIRED:")) {
            const jsonStr = kemungkinanTeks.slice("[TOOL_CONFIRM_REQUIRED:".length, -1);
            try {
                const daftarAksi = JSON.parse(jsonStr);
                renderToolConfirmCard(textNode, daftarAksi, currentSessionId);
            } catch (e) {
                textNode.innerHTML = "⚠️ Gagal membaca permintaan konfirmasi.";
            }
            eventSource.close();
            return;
        }

        if (event.data === "[DONE]") {
            eventSource.close();
            setIsFirstChat(false);
            loadSessions();
            setTimeout(loadSessions, 2500); // refresh susulan buat nangkep judul async
            highlightCodeDenganRetry(textNode);
            return;
        }

        if (isFirstToken) {
            textNode.innerHTML = "";
            isFirstToken = false;
        }

        let tokenMurni = "";
        try {
            const dataObj = JSON.parse(event.data);
            if (dataObj && dataObj.text !== undefined) tokenMurni = dataObj.text;
            else tokenMurni = event.data;
        } catch(e) {
            tokenMurni = event.data;
        }

        accumulatedText += tokenMurni.replace(/\[NEWLINE\]/g, '\n');
        textNode.innerHTML = formatMarkdownToHtml(accumulatedText);

        const container = document.getElementById('chatContainer');
        if (container) container.scrollTop = container.scrollHeight;
    };

    eventSource.onerror = function() {
        textNode.innerHTML = "⚠️ Error streaming data dari Neira Ecosystem.";
        eventSource.close();
    };
}

export async function kirimPesanDenganTeks(text) {
    const welcome = document.getElementById('welcomeScreen');
    if (welcome) welcome.classList.add('hidden');
    document.getElementById('sidebar').classList.add('collapsed');

    appendBubble(text, true);

    const responseRow = appendBubble('<span class="thinking-dots">...</span>', false);
    const textNode = responseRow.querySelector(".neira-text");

    const encText = encodeURIComponent(text);
    const eventSource = new EventSource(`/api/chat-stream?pesan=${encText}&session_id=${currentSessionId || ''}`);

    let isFirstToken = true;
    let accumulatedText = "";

    eventSource.onmessage = function(event) {
        if (event.data.startsWith("[SESSION_ID_ASSIGNED:")) {
            const extractedId = event.data.match(/\d+/)[0];
            setSessionId(parseInt(extractedId));
            return;
        }

        // Deteksi sinyal minta konfirmasi tool (parse JSON envelope dulu)
        let kemungkinanTeks = "";
        try {
            const dataObjCek = JSON.parse(event.data);
            kemungkinanTeks = dataObjCek.text || "";
        } catch (e) {
            kemungkinanTeks = "";
        }

        if (kemungkinanTeks.startsWith("[TOOL_CONFIRM_REQUIRED:")) {
            const jsonStr = kemungkinanTeks.slice("[TOOL_CONFIRM_REQUIRED:".length, -1);
            try {
                const daftarAksi = JSON.parse(jsonStr);
                renderToolConfirmCard(textNode, daftarAksi, currentSessionId);
            } catch (e) {
                textNode.innerHTML = "⚠️ Gagal membaca permintaan konfirmasi.";
            }
            eventSource.close();
            return;
        }

        if (event.data === "[DONE]") {
            eventSource.close();
            setIsFirstChat(false);
            loadSessions();
            setTimeout(loadSessions, 2500); // refresh susulan buat nangkep judul async
            highlightCodeDenganRetry(textNode);
            return;
        }

        if (isFirstToken) {
            textNode.innerHTML = "";
            isFirstToken = false;
        }

        let tokenMurni = "";
        try {
            const dataObj = JSON.parse(event.data);
            if (dataObj && dataObj.text !== undefined) tokenMurni = dataObj.text;
            else tokenMurni = event.data;
        } catch(e) {
            tokenMurni = event.data;
        }

        accumulatedText += tokenMurni.replace(/\[NEWLINE\]/g, '\n');
        textNode.innerHTML = formatMarkdownToHtml(accumulatedText);
        
        const container = document.getElementById('chatContainer');
        if (container) container.scrollTop = container.scrollHeight;
    };

    eventSource.onerror = function() {
        textNode.innerHTML = "⚠️ Error streaming data dari Neira Ecosystem.";
        eventSource.close();
    };
}

export function appendBubble(text, isUser) {
    const container = document.getElementById('chatContainer');
    if (!container) return;

    const row = document.createElement('div');
    row.className = isUser ? 'chat-row user-row' : 'chat-row neira-row';

    let processedText = isUser ? text : formatMarkdownToHtml(text);
    if (!isUser && text.includes("thinking-dots")) {
        processedText = text;
    }

    row.innerHTML = isUser ?
        `<div class="user-bubble">${processedText}</div>` :
        `<div class="neira-text">${processedText}</div>`;

    container.appendChild(row);
    container.scrollTop = container.scrollHeight;
    return row;
}

export function renderToolConfirmCard(textNode, daftarAksi, sessionId) {
    const isWorkflow = daftarAksi.length === 1 && daftarAksi[0].type === 'workflow';

    // AMBIL KONTEKS: Cari bubble chat terakhir milik user
    const userBubbles = document.querySelectorAll('.user-bubble');
    let userContextText = "";
    if (userBubbles.length > 0) {
        userContextText = userBubbles[userBubbles.length - 1].innerText.trim();
    }

    if (isWorkflow) {
        const item = daftarAksi[0];
        let kalimatKonfirmasi = `Create a workflow for "${item.title || item.label || 'New Task'}"?`;
        
        if (userContextText) {
            let cleanContext = userContextText
                .replace(/^(tolong|bantu|buatkan|setup|create|please)\s+/i, '') 
                .replace(/\?$/, '')
                .replace(/\bme\b/gi, 'you')
                .replace(/\bmy\b/gi, 'your');
            
            kalimatKonfirmasi = `Create workflow to ${cleanContext}?`;
        }

        // KITA HILANGKAN .tool-confirm-wrapper YANG TIDAK PERLU
        textNode.innerHTML = `
            <div class="tool-confirm-card">
                <p class="tool-confirm-desc">${kalimatKonfirmasi}</p>
                <div class="tool-confirm-buttons">
                    <button class="tool-confirm-cancel">Cancel</button>
                    <button class="tool-confirm-run">Execute</button>
                </div>
            </div>`;
    } else {
        const listHtml = daftarAksi.map(a => `<li>${a.label}</li>`).join('');
        const judul = daftarAksi.length > 1 ? "Here's what I'll do:" : "Confirm action:";
        textNode.innerHTML = `
            <div class="tool-confirm-card">
                <p class="tool-confirm-title">${judul}</p>
                <ul class="tool-confirm-list">${listHtml}</ul>
                <div class="tool-confirm-buttons">
                    <button class="tool-confirm-cancel">Cancel</button>
                    <button class="tool-confirm-run">Confirm</button>
                </div>
            </div>`;
    }

    const cancelBtn = textNode.querySelector('.tool-confirm-cancel');
    const runBtn = textNode.querySelector('.tool-confirm-run');

    cancelBtn.addEventListener('click', async () => {
        textNode.innerHTML = '<span class="thinking-dots">Membatalkan...</span>';
        await fetch('/api/tool-cancel', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId })
        });
        textNode.innerHTML = '<em>Aksi dibatalkan.</em>';
    });

    runBtn.addEventListener('click', () => {
        textNode.innerHTML = '<span class="thinking-dots">Menjalankan...</span>';
        const es = new EventSource(`/api/tool-confirm-stream?session_id=${sessionId}`);
        let isFirst = true;
        let acc = "";

        es.onmessage = (event) => {
            if (event.data === "[DONE]") {
                es.close();
                return;
            }
            if (isFirst) { textNode.innerHTML = ""; isFirst = false; }
            try {
                const obj = JSON.parse(event.data);
                acc += (obj.text || '').replace(/\[NEWLINE\]/g, '\n');
                textNode.innerHTML = acc;
            } catch (e) {}
        };
        es.onerror = () => es.close();
    });
}