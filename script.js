// ==================== GERBANG UTAMA (ENTRY POINT) ====================
import { injectModalsAndToasts } from './js/ui.js';
import { loadSessions, switchSession, renameSession, deleteSession, currentSessionId, setSessionId, setIsFirstChat } from './js/session.js';
import { kirimPesan } from './js/chat.js';
import { uploadDokumen, uploadGambar } from './js/upload.js';

document.addEventListener("DOMContentLoaded", () => {
    // 1. Inisialisasi Tampilan & Sesi Awal
    loadSessions();
    injectModalsAndToasts();

    // Helper aman untuk memasang event listener
    const safeAddListener = (id, event, callback) => {
        const element = document.getElementById(id);
        if (element) element.addEventListener(event, callback);
    };

    // 2. Event Listener: Sidebar & New Chat
    safeAddListener('menuBtn', 'click', () => {
        document.getElementById('sidebar').classList.toggle('collapsed');
    });

    safeAddListener('newChatBtn', 'click', () => {
        setSessionId(null);
        setIsFirstChat(true);
        const chatContainer = document.getElementById('chatContainer');
        if (chatContainer) {
            chatContainer.innerHTML = `
                <div class="welcome-screen" id="welcomeScreen">
                    <h1 class="animate-fade-up">Hello, Ian</h1>
                    <p class="animate-fade-up-delay">How can I assist your tech journey today?</p>
                </div>`;
        }
        loadSessions();
        const inputArea = document.getElementById('userInput');
        if (inputArea) inputArea.focus();
    });

    // 3. Event Listener: Input & Kirim Pesan
    safeAddListener('userInput', 'keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            kirimPesan();
        }
    });

    safeAddListener('sendBtn', 'click', kirimPesan);

    // 4. Event Listener: Upload File & Gambar (Manual via Klik)
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

    // 5. Event Listener: Drag & Drop Area Chat PINTAR
    const dropZone = document.getElementById('chatContainer');
    if (dropZone) {
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('drag-over');
        });
        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('drag-over');
        });
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('drag-over');
            
            if (e.dataTransfer.files.length > 0) {
                const fileTerdrop = e.dataTransfer.files[0];
                const tipeFile = fileTerdrop.type;

                if (tipeFile.startsWith('image/')) {
                    uploadGambar(fileTerdrop);
                } else {
                    uploadDokumen(fileTerdrop);
                }
            }
        });
    }

    // 6. Otomatis fokus ke textarea saat Neira dijalankan pertama kali
    const inputArea = document.getElementById('userInput');
    if (inputArea) inputArea.focus();
});

// Beacon shutdown tetap ditaruh secara global di pintu utama
window.addEventListener('beforeunload', () => {
    navigator.sendBeacon('/api/shutdown');
});