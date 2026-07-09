// js/chat.js
import { autoGrow, formatMarkdownToHtml } from './ui.js';
import { currentSessionId, loadSessions, setSessionId, setIsFirstChat } from './session.js';

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

        if (event.data === "[DONE]") {
            eventSource.close();
            setIsFirstChat(false);
            loadSessions();
            if (window.Prism) {
                textNode.querySelectorAll('code[class*="language-"]').forEach(el => {
                    Prism.highlightElement(el);
                });
            }
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

        if (event.data === "[DONE]") {
            eventSource.close();
            setIsFirstChat(false);
            loadSessions();
            if (window.Prism) {
                textNode.querySelectorAll('code[class*="language-"]').forEach(el => {
                    Prism.highlightElement(el);
                });
            }
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