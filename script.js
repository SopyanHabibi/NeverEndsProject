// ==================== GERBANG UTAMA (ENTRY POINT) ====================
import { injectModalsAndToasts } from './js/ui.js';
import { loadSessions, currentSessionId, setSessionId, setIsFirstChat, switchSession } from './js/session.js';
import { kirimPesan, kirimPesanDenganTeks } from './js/chat.js';
import { uploadDokumen, uploadGambar } from './js/upload.js';
import { appendBubble } from './js/chat.js';

// --- FUNGSI GENERATOR GREETING DINAMIS (WAKTU + ACAK) ---
function getDynamicWelcomeContent() {
    // 1. Logika Opsi 2: Sapaan berdasarkan waktu lokal (Tetap personal ada nama Ian)
    const hours = new Date().getHours();
    let greetingTitle = "Hello, Ian"; // Default fallback

    if (hours >= 5 && hours < 12) {
        greetingTitle = "Good morning, Ian";
    } else if (hours >= 12 && hours < 17) {
        greetingTitle = "Good afternoon, Ian";
    } else if (hours >= 17 && hours < 21) {
        greetingTitle = "Good evening, Ian";
    } else if (hours >= 21 || hours < 5) {
        // Vibe buat nemenin kamu kalau lagi ngoding tengah malam
        greetingTitle = "Hello, Late Night Coder Ian"; 
    }

    // 2. Logika Opsi 1: Kalimat penjelas acak (Tech & Code vibe)
    const subtitles = [
        "How can I assist your tech journey today?",
        "Ready to squash some bugs or write something epic?",
        "What are we building or configuring today?",
        "Let's turn your logic into running code.",
        "Need help with an architecture, script, or a quick debug?"
    ];
    const randomIndex = Math.floor(Math.random() * subtitles.length);
    const chosenSubtitle = subtitles[randomIndex];

    return { title: greetingTitle, subtitle: chosenSubtitle };
}

function showCodeQuestionModal(fileName, codeSnippet) {
    return new Promise((resolve) => {
        const modal = document.getElementById('codeQuestionModal');
        const input = document.getElementById('codeQuestionInput');
        const fileLabel = document.getElementById('codeQuestionFileLabel');
        const snippetEl = document.getElementById('codeQuestionSnippet');
        const submitBtn = document.getElementById('codeQuestionSubmit');
        const cancelBtn = document.getElementById('codeQuestionCancel');

        input.value = "";
        fileLabel.textContent = fileName;
        snippetEl.textContent = codeSnippet || "(no code selected)";
        modal.classList.add('active');
        input.focus();

        const handleSubmit = () => {
            const value = input.value.trim();
            cleanup();
            resolve(value || "Can you analyze this code and explain what it does or what might be wrong?");
        };
        const handleCancel = () => { cleanup(); resolve(null); };
        const handleKeypress = (e) => { if (e.key === 'Enter') handleSubmit(); };
        const cleanup = () => {
            modal.classList.remove('active');
            submitBtn.removeEventListener('click', handleSubmit);
            cancelBtn.removeEventListener('click', handleCancel);
            input.removeEventListener('keypress', handleKeypress);
        };

        submitBtn.addEventListener('click', handleSubmit);
        cancelBtn.addEventListener('click', handleCancel);
        input.addEventListener('keypress', handleKeypress);
    });
}

async function handleIncomingVsCodeContext(ctx) {
    setSessionId(ctx.session_id);
    setIsFirstChat(false);
    await switchSession(ctx.session_id);

    const pertanyaan = await showCodeQuestionModal(ctx.fileName, ctx.selectedCode);
    if (pertanyaan === null) return; // user cancel, tidak kirim apa-apa

    let promptLengkap = `I need help with this code from \`${ctx.fileName}\`.\n\n`;
    if (ctx.selectedCode) {
        promptLengkap += `\`\`\`\n${ctx.selectedCode}\n\`\`\`\n\n`;
    }
    if (ctx.errorMessage) {
        promptLengkap += `Detected issue: ${ctx.errorMessage}\n\n`;
    }
    promptLengkap += pertanyaan;

    kirimPesanDenganTeks(promptLengkap);
}

function listenToLiveSession(sessionId) {
    const container = document.getElementById('chatContainer');
    const responseRow = appendBubble('<span class="thinking-dots">...</span>', false);
    const textNode = responseRow.querySelector('.neira-text');

    const es = new EventSource(`/api/session-stream?session_id=${sessionId}`);
    let isFirstToken = true;
    let accumulated = "";

    es.onmessage = (event) => {
        if (event.data === "[DONE]") {
            es.close();
            return;
        }
        if (isFirstToken) { textNode.innerHTML = ""; isFirstToken = false; }
        try {
            const obj = JSON.parse(event.data);
            const clean = (obj.text || '').replace(/\[NEWLINE\]/g, '\n');
            accumulated += clean;
            textNode.innerHTML = accumulated;
            container.scrollTop = container.scrollHeight;
        } catch (e) {}
    };
    es.onerror = () => es.close();
}

// --- ENGINE UTAMA DOM LOADED ---
document.addEventListener("DOMContentLoaded", () => {
    loadSessions();
    injectModalsAndToasts();


    // BARU: polling cek apakah ada sesi baru dari VS Code
    setInterval(async () => {
        try {
            const res = await fetch('/api/vscode/pending');
            const data = await res.json();
            if (data && data.session_id) {
                handleIncomingVsCodeContext(data);
            }
        } catch (e) { /* diamkan */ }
    }, 3000);

    // Jalankan greeting dinamis untuk tampilan AWAL saat aplikasi pertama dimuat (Refresh)
    const chatContainer = document.getElementById('chatContainer');
    if (chatContainer && !currentSessionId) {
        const welcomeData = getDynamicWelcomeContent();
        chatContainer.innerHTML = `
            <div class="welcome-screen" id="welcomeScreen">
                <h1 class="animate-fade-up">${welcomeData.title}</h1>
                <p class="animate-fade-up-delay">${welcomeData.subtitle}</p>
            </div>`;
    }

    const safeAddListener = (id, event, callback) => {
        const element = document.getElementById(id);
        if (element) element.addEventListener(event, callback);
    };

    // Event Listener: New Chat Button (Kombinasi Sempurna Opsi 1 + Opsi 2)
    safeAddListener('newChatBtn', 'click', () => {
        setSessionId(null);
        setIsFirstChat(true);
        
        const container = document.getElementById('chatContainer');
        if (container) {
            // Ambil konten fresh (waktu saat ini + subtitle acak baru)
            const welcomeData = getDynamicWelcomeContent();
            
            container.innerHTML = `
                <div class="welcome-screen" id="welcomeScreen">
                    <h1 class="animate-fade-up">${welcomeData.title}</h1>
                    <p class="animate-fade-up-delay">${welcomeData.subtitle}</p>
                </div>`;
        }
        
        loadSessions();
        const inputArea = document.getElementById('userInput');
        if (inputArea) inputArea.focus();
    });

    // --- Sisa Event Listener Bawaan Kamu di Bawah ( userInput, sendBtn, uploadBtn, dsb ) ---
    safeAddListener('userInput', 'keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            kirimPesan();
        }
    });

    safeAddListener('sendBtn', 'click', kirimPesan);

    safeAddListener('menuBtn', 'click', (e) => {
        e.preventDefault(); // Mencegah glitch jika tombol berupa tag anchor/link
        const sidebar = document.getElementById('sidebar');
        if (sidebar) {
            sidebar.classList.toggle('collapsed');
            console.log("Sidebar status collapsed:", sidebar.classList.contains('collapsed')); // Untuk debugging di console browser
        } else {
            console.error("Kritis: Elemen dengan id='sidebar' tidak ditemukan di HTML!");
        }
    });

    safeAddListener('uploadBtn', 'click', () => {
        const fileInput = document.getElementById('fileInput');
        if (fileInput) fileInput.click();
    });
    
    safeAddListener('fileInput', 'change', (e) => {
        if (e.target.files.length > 0) uploadDokumen(e.target.files[0]);
    });
    
    safeAddListener('imageBtn', 'click', () => {
        const imageInput = document.getElementById('imageInput');
        if (imageInput) imageInput.click();
    });
    
    safeAddListener('imageInput', 'change', (e) => {
        if (e.target.files.length > 0) uploadGambar(e.target.files[0]);
    });

    const dropZone = document.getElementById('chatContainer');
    if (dropZone) {
        dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('drag-over'); });
        dropZone.addEventListener('dragleave', () => { dropZone.classList.remove('drag-over'); });
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('drag-over');
            if (e.dataTransfer.files.length > 0) {
                const fileTerdrop = e.dataTransfer.files[0];
                if (fileTerdrop.type.startsWith('image/')) { uploadGambar(fileTerdrop); } 
                else { uploadDokumen(fileTerdrop); }
            }
        });
    }

    const inputArea = document.getElementById('userInput');
    if (inputArea) inputArea.focus();
});

window.addEventListener('beforeunload', () => {
    navigator.sendBeacon('/api/shutdown');
});