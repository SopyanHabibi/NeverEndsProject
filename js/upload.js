// js/upload.js
import { showMiniAlert } from './ui.js';
import { currentSessionId, loadSessions, setSessionId } from './session.js';
import { appendBubble } from './chat.js';

export async function uploadDokumen(file) {
    const ekstensi = file.name.split('.').pop().toLowerCase();
    if (!['pdf', 'docx', 'pptx'].includes(ekstensi)) {
        showMiniAlert("Cuma support PDF, DOCX, atau PPTX ya, Ian.");
        return;
    }

    if (!currentSessionId) {
        showMiniAlert("Kirim satu pesan teks terlebih dahulu untuk membuka sesi obrolan, Ian!");
        return;
    }

    const reader = new FileReader();
    reader.onload = async () => {
        const base64 = reader.result.split(',')[1];
        appendBubble(`📄 Uploading <b>${file.name}</b>...`, false);

        try {
            const response = await fetch('/api/upload-document', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    session_id: currentSessionId,
                    filename: file.name,
                    filedata: base64
                })
            });
            const hasil = await response.json();

            if (hasil.status === 'success') {
                appendBubble(`✅ <b>${hasil.filename}</b> has been uploaded successfully!`, false);
            } else {
                appendBubble(`❌ Upload failed: ${hasil.message}`, false);
            }
        } catch (error) {
            console.error("Gagal upload dokumen:", error);
            appendBubble(`❌ Upload failed: Connection error.`, false);
        }
    };
    reader.readAsDataURL(file);
}

export async function uploadGambar(file) {
    const tipeValid = ['image/jpeg', 'image/png', 'image/webp'];
    if (!tipeValid.includes(file.type)) {
        showMiniAlert("Cuma support JPG, PNG, atau WEBP ya, Ian.");
        return;
    }

    const reader = new FileReader();
    reader.onload = async () => {
        const base64 = reader.result.split(',')[1];
        const dataUrlGambar = reader.result;

        const pertanyaan = await showCustomPrompt(
            "What would you like to know about this image? (Leave blank for a general description)", 
            dataUrlGambar
        );

        appendBubble(`<img src="${dataUrlGambar}" style="max-width:250px; border-radius:12px; margin-bottom:8px;"><br>${pertanyaan}`, true);
        const loadingRow = appendBubble('<span class="thinking-dots">Analyzing image...</span>', false);
        const textNode = loadingRow.querySelector(".neira-text");

        try {
            const response = await fetch('/api/upload-image', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: currentSessionId,
                    pertanyaan: pertanyaan,
                    filedata: base64,
                    filename: file.name
                })
            });

            const hasil = await response.json();

            if (hasil.status === 'success') {
                setSessionId(hasil.session_id);
                textNode.innerHTML = hasil.deskripsi;
                loadSessions();
            } else {
                textNode.innerHTML = `❌ Image analysis failed: ${hasil.message}`;
            }
        } catch (e) {
            textNode.innerHTML = `⚠️ Error: ${e.message}`;
        }
    };
    reader.readAsDataURL(file);
}

function showCustomPrompt(message, imgSrc) {
    return new Promise((resolve) => {
        const modal = document.getElementById('customPromptModal');
        const input = document.getElementById('customPromptInput');
        const previewImg = document.getElementById('customPromptPreview');
        const submitBtn = document.getElementById('customPromptSubmit');
        const cancelBtn = document.getElementById('customPromptCancel');
        const textMessage = document.getElementById('customPromptMessage');

        textMessage.textContent = message;
        input.value = ""; 
        previewImg.src = imgSrc;
        
        modal.classList.add('active');
        input.focus();

        const handleSubmit = () => {
            const value = input.value.trim();
            cleanup();
            resolve(value || "Describe this image in detail.");
        };
        const handleCancel = () => { cleanup(); resolve("Describe this image in detail."); };
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