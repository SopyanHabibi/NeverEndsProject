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
                <h1 class="animate-fade-up">Hello, Ian</h1>
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

// Upload dokumen via tombol
    document.getElementById('uploadBtn').addEventListener('click', () => {
        document.getElementById('fileInput').click();
    });
    document.getElementById('fileInput').addEventListener('change', (e) => {
        if (e.target.files.length > 0) uploadDokumen(e.target.files[0]);
    });
    
    document.getElementById('imageBtn').addEventListener('click', () => {
        document.getElementById('imageInput').click();
    });
    document.getElementById('imageInput').addEventListener('change', (e) => {
        if (e.target.files.length > 0) uploadGambar(e.target.files[0]);
    });

    // Upload dokumen via drag & drop ke area chat
    const dropZone = document.getElementById('chatContainer');
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
        if (e.dataTransfer.files.length > 0) uploadDokumen(e.dataTransfer.files[0]);
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
                <div class="history-title" onclick="switchSession(${idSesi})">${judulSesi}</div>
                <div class="history-actions">
                    <button class="action-btn" onclick="renameSession(${idSesi})">✏️</button>
                    <button class="action-btn" onclick="deleteSession(${idSesi}, '${judulSesi.replace(/'/g, "\\'")}')">🗑️</button>
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
    // 1. Cari elemen penampung item history berdasarkan fungsi switchSession yang dipanggil
    // Kita cari button yang memicu fungsi ini, lalu mundur ke parent-nya (.history-item)
    const buttonClicked = document.querySelector(`button[onclick^="renameSession(${id})"]`);
    if (!buttonClicked) return;

    const historyItem = buttonClicked.closest('.history-item');
    const titleElement = historyItem.querySelector('.history-title');
    const originalTitle = titleElement.textContent.trim();

    // 2. Buat elemen input baru untuk menggantikan teks sementara
    const inputElement = document.createElement('input');
    inputElement.type = 'text';
    inputElement.className = 'history-rename-input';
    inputElement.value = originalTitle;

    // Sembunyikan element judul asli, lalu masukkan input tepat di atasnya
    titleElement.style.display = 'none';
    titleElement.parentNode.insertBefore(inputElement, titleElement);

    // 3. Fokus ke input dan BLOK seluruh karakter di dalamnya
    inputElement.focus();
    inputElement.select(); // Ini yang bikin semua teks langsung ter-highlight/blok

    // Fungsi pembantu untuk menyimpan perubahan judul baru
    let isSaved = false; // Flag mencegah double-trigger antara Enter dan Blur
    const saveChanges = async () => {
        if (isSaved) return;
        isSaved = true;

        const newTitle = inputElement.value.trim();

        // Jika kosong atau sama dengan judul asli, batalkan proses save dan kembalikan ke awal
        if (!newTitle || newTitle === originalTitle) {
            titleElement.style.display = 'block';
            inputElement.remove();
            return;
        }

        // Tampilkan feedback visual instan di UI sembari nunggu fetch backend selesai
        titleElement.textContent = newTitle;
        titleElement.style.display = 'block';
        inputElement.remove();

        try {
            // Kirim data ke API backend SQLite kamu
            await fetch('/api/session/rename', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id: id, title: newTitle })
            });
            
            // Refresh list session agar event listener di render ulang dengan judul baru
            loadSessions();
        } catch (error) {
            console.error("Gagal mengubah nama sesi:", error);
            titleElement.textContent = originalTitle; // Rollback jika gagal
        }
    };

    // 4. EVENT LISTENERS: Jalankan save jika pencet Enter atau Klik di luar area input
    inputElement.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            saveChanges();
        } else if (e.key === 'Escape') {
            // Jika pencet Esc, batalkan tanpa menyimpan
            isSaved = true;
            titleElement.style.display = 'block';
            inputElement.remove();
        }
    });

    inputElement.addEventListener('blur', () => {
        saveChanges();
    });
}

async function deleteSession(id, namaChat = "this chat") {
    
    // Panggil custom modal ganti confirm bawaan browser
    const konfirmasi = await showDeleteConfirmation(namaChat);
    
    // Jika klik Cancel, batalkan proses
    if (!konfirmasi) return;

    // Jika klik Delete, lanjutkan eksekusi ke backend
    try {
        await fetch('/api/session/delete', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ id: id })
        });
        
        if (id === currentSessionId) {
            document.getElementById('newChatBtn').click();
        } else {
            loadSessions();
        }
    } catch (error) {
        console.error("Gagal menghapus obrolan:", error);
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

    const responseRow = appendBubble('<span class="thinking-dots">...</span>', false);
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
        `<div class="neira-text">${processedText}</div>`;
        
    container.appendChild(row);
    container.scrollTop = container.scrollHeight;
    return row;
}

async function uploadDokumen(file) {
    const ekstensi = file.name.split('.').pop().toLowerCase();
    if (!['pdf', 'docx', 'pptx'].includes(ekstensi)) {
        showMiniAlert("Cuma support PDF, DOCX, atau PPTX ya, Ian.");
        return;
    }

    // Pastikan ada session_id aktif dulu (buat sesi baru kalau belum ada)
    if (!currentSessionId) {
        const res = await fetch('/api/chat-stream?pesan=&session_id=');
        // fallback simple: minta user kirim 1 chat dulu kalau belum ada sesi
    }

    const reader = new FileReader();
    reader.onload = async () => {
        const base64 = reader.result.split(',')[1];
        appendBubble(`📄 Uploading <b>${file.name}</b>...`, false);

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
            appendBubble(`✅ <b>${hasil.filename}</b> has been uploaded and processed successfully (${hasil.chunks} chunks). Feel free to ask anything about its contents, request a summary, or even generate a quiz!`, false);
        } else {
            appendBubble(`❌ Upload failed: ${hasil.message}`, false);
        }
    };
    reader.readAsDataURL(file);
}

// 1. INJECTOR MODAL (Gabungkan bagian dalam DOMContentLoaded ini dengan yang sudah ada)
document.addEventListener("DOMContentLoaded", () => {
    // Kode modal upload gambar kamu yang kemarin tetap biarkan ada disini...
    const modalHTML = `
        <div id="customPromptModal" class="modal-overlay">
            <div class="modal-box">
                <!-- Sisi Kiri: Gambar -->
                <div class="modal-preview-side">
                    <img id="customPromptPreview" src="" alt="Preview">
                </div>
                <!-- Sisi Kanan: Input Form -->
                <div class="modal-form-side">
                    <p id="customPromptMessage">What would you like to know about this image?</p>
                    <input type="text" id="customPromptInput" autocomplete="off" placeholder="Ask Neira anything about this image...">
                    <div class="modal-buttons">
                        <button id="customPromptCancel" class="btn-cancel">Skip / Default</button>
                        <button id="customPromptSubmit" class="btn-submit">Submit</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', modalHTML);

    // Tambahkan modal konfirmasi hapus ini di bawahnya:
    const confirmModalHTML = `
        <div id="customConfirmModal" class="confirm-overlay">
            <div class="confirm-box">
                <h3>Delete chat?</h3>
                <p id="confirmMessage">This will delete <strong>Chat Name</strong>.</p>
                <div class="confirm-buttons">
                    <button id="confirmCancelBtn" class="btn-confirm-cancel">Cancel</button>
                    <button id="confirmDeleteBtn" class="btn-confirm-delete">Delete</button>
                </div>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', confirmModalHTML);
    
});

// 1. INJECTOR TOAST MINI (Masukkan ke dalam kontainer input-wrapper saat DOM siap)
document.addEventListener("DOMContentLoaded", () => {
    const inputWrapper = document.querySelector('.input-wrapper');
    if (inputWrapper) {
        // Membuat element div untuk toast secara dinamis
        const toastHTML = `
            <div id="miniAlertToast" class="toast-container">
                <i class="fa-solid fa-triangle-exclamation"></i>
                <span id="toastMessage">Pesan error di sini</span>
            </div>
        `;
        // Diselipkan di bagian paling atas di dalam .input-wrapper
        inputWrapper.insertAdjacentHTML('afterbegin', toastHTML);
    }
});

// 2. HELPER FUNCTION UNTUK MENAMPILKAN POP-UP MINI (Auto-hide dalam 3.5 detik)
let toastTimeout;
function showMiniAlert(message) {
    const toast = document.getElementById('miniAlertToast');
    const toastMsg = document.getElementById('toastMessage');
    
    if (!toast || !toastMsg) return;

    // Bersihkan timeout lama jika user klik berkali-kali sebelum toast hilang
    clearTimeout(toastTimeout);

    // Set pesan teks terbaru
    toastMsg.textContent = message;

    // Tampilkan toast ke layar
    toast.classList.add('show');

    // Sembunyikan otomatis setelah 3.5 detik
    toastTimeout = setTimeout(() => {
        toast.classList.remove('show');
    }, 3500);
}

// 2. HELPER FUNCTION (Mengontrol buka/tutup modal lewat Promise)
function showDeleteConfirmation(namaChat) {
    return new Promise((resolve) => {
        const modal = document.getElementById('customConfirmModal');
        const messageEl = document.getElementById('confirmMessage');
        const cancelBtn = document.getElementById('confirmCancelBtn');
        const deleteBtn = document.getElementById('confirmDeleteBtn');

        // Set teks persis seperti referensi image_734716.png
        messageEl.innerHTML = `This will delete <strong>${namaChat}</strong>.<br><span style="font-size:0.85rem; opacity:0.6; display:block; margin-top:8px;">Visit <span class="settings-link" style="text-decoration: underline;">settings</span> to delete any memories saved during this chat.</span>`;

        // Tampilkan modal
        modal.classList.add('active');

        const onDelete = () => {
            cleanup();
            resolve(true); // User klik Delete
        };

        const onCancel = () => {
            cleanup();
            resolve(false); // User klik Cancel
        };

        const cleanup = () => {
            modal.classList.remove('active');
            deleteBtn.removeEventListener('click', onDelete);
            cancelBtn.removeEventListener('click', onCancel);
        };

        deleteBtn.addEventListener('click', onDelete);
        cancelBtn.addEventListener('click', onCancel);
    });
}

// 2. HELPER FUNCTION (Menerima parameter imgSrc agar bisa nampilin gambar)
function showCustomPrompt(message, imgSrc) {
    return new Promise((resolve) => {
        const modal = document.getElementById('customPromptModal');
        const input = document.getElementById('customPromptInput');
        const previewImg = document.getElementById('customPromptPreview');
        const submitBtn = document.getElementById('customPromptSubmit');
        const cancelBtn = document.getElementById('customPromptCancel');
        const textMessage = document.getElementById('customPromptMessage');

        // Set konten pesan, input reset, dan taruh source gambar ke previewer
        textMessage.textContent = message;
        input.value = ""; 
        previewImg.src = imgSrc; // Pasang gambarnya di sini
        
        modal.classList.add('active');
        input.focus();

        const handleSubmit = () => {
            const value = input.value.trim();
            cleanup();
            resolve(value || "Describe this image in detail.");
        };

        const handleCancel = () => {
            cleanup();
            resolve("Describe this image in detail.");
        };

        const handleKeypress = (e) => {
            if (e.key === 'Enter') handleSubmit();
        };

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

// 3. FUNGSI UTAMA UPLOAD GAMBAR KAMU
async function uploadGambar(file) {
    const tipeValid = ['image/jpeg', 'image/png', 'image/webp'];
    if (!tipeValid.includes(file.type)) {
        alert("Only JPG, PNG, and WEBP images are supported.");
        return;
    }

    const reader = new FileReader();
    reader.onload = async () => {
        const base64 = reader.result.split(',')[1];
        const dataUrlGambar = reader.result; // Dapatkan string base64 full untuk preview

        // KITA PANGGIL MODAL DI SINI (Melemparkan dataUrlGambar ke dalam modal agar tampil di sebelah kiri)
        const pertanyaan = await showCustomPrompt(
            "What would you like to know about this image? (Leave blank for a general description)", 
            dataUrlGambar
        );

        // Setelah user isi prompt modal, alur chat berjalan ke bawah seperti biasa
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
                currentSessionId = hasil.session_id;
                textNode.innerHTML = formatMarkdownToHtml(hasil.deskripsi);
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


// AMAN: Bagian shutdown beacon kita hapus total dari sini agar pas di-refresh Neira TIDAK MATI!

// Sinyal mati otomatis ketika tab web ditutup oleh user
window.addEventListener('beforeunload', () => {
    navigator.sendBeacon('/api/shutdown');
});