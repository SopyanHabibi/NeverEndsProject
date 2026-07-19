// js/session.js
import { appendBubble, highlightCodeDenganRetry } from './chat.js';

export let currentSessionId = null;
export let isFirstChatInSession = true;

export function setSessionId(id) { currentSessionId = id; }
export function setIsFirstChat(status) { isFirstChatInSession = status; }

// Helper function untuk merender item ke dalam kontainer tertentu
function renderItemsToContainer(sessions, container, placeholderText = "No chats") {
    container.innerHTML = '';
    
    if (!sessions || !Array.isArray(sessions) || sessions.length === 0) {
        container.innerHTML = `<div class="no-data-placeholder">${placeholderText}</div>`;
        return;
    }

    sessions.forEach(s => {
        const idSesi = s.session_id;
        const judulSesi = s.judul;
        if (!idSesi || !judulSesi) return;

        const item = document.createElement('div');
        item.className = `history-item ${idSesi === currentSessionId ? 'active' : ''}`;
        
        // Masukkan fungsi pemicu global agar aman dieksekusi dari HTML
        window.triggerSwitchSession = switchSession;
        window.triggerRenameSession = renameSession;
        window.triggerDeleteSession = deleteSession;

        item.innerHTML = `
            <div class="history-title" onclick="window.triggerSwitchSession(${idSesi})">${judulSesi}</div>
            <div class="history-actions">
                <button class="action-btn" onclick="window.triggerRenameSession(${idSesi})">✏️</button>
                <button class="action-btn" onclick="window.triggerDeleteSession(${idSesi}, '${judulSesi.replace(/'/g, "\\'")}')">🗑️</button>
            </div>`;
        container.appendChild(item);
    });
}

export async function loadSessions() {
    try {
        // 1. Ambil data kontainer HTML
        const generalContainer = document.getElementById('generalList');
        const projectContainer = document.getElementById('projectList');
        if (!generalContainer || !projectContainer) return;

        // 2. Fetch data dari backend secara paralel (memanfaatkan endpoint terpisah)
        const [resGeneral, resProject] = await Promise.all([
            fetch('/api/sessions?kategori=general'),
            fetch('/api/sessions?kategori=project')
        ]);

        const generalSessions = await resGeneral.json();
        const projectSessions = await resProject.json();

        // 3. Render masing-masing data ke kontainernya
        renderItemsToContainer(generalSessions, generalContainer, "No chats");
        renderItemsToContainer(projectSessions, projectContainer, "No projects");

    } catch (e) { 
        console.error("Gagal memuat histori kategori", e); 
    }
}

export async function switchSession(id) {
    currentSessionId = id;
    isFirstChatInSession = false;
    document.getElementById('sidebar').classList.add('collapsed');
    
    const response = await fetch(`/api/history?session_id=${id}`);
    const history = await response.json();
    
    const container = document.getElementById('chatContainer');
    if (container) container.innerHTML = '';
    
    if (history && Array.isArray(history)) {
        history.forEach(chat => {
            appendBubble(chat.content, chat.role === 'user');
        });
    }

    highlightCodeDenganRetry(container); // BARU: highlight semua code block di history yang baru di-render

    loadSessions();
}

export async function renameSession(id) {
    const buttonClicked = document.querySelector(`button[onclick^="window.triggerRenameSession(${id})"]`);
    if (!buttonClicked) return;

    const historyItem = buttonClicked.closest('.history-item');
    const titleElement = historyItem.querySelector('.history-title');
    const originalTitle = titleElement.textContent.trim();

    const inputElement = document.createElement('input');
    inputElement.type = 'text';
    inputElement.className = 'history-rename-input';
    inputElement.value = originalTitle;

    titleElement.style.display = 'none';
    titleElement.parentNode.insertBefore(inputElement, titleElement);

    inputElement.focus();
    inputElement.select();

    let isSaved = false;
    const saveChanges = async () => {
        if (isSaved) return;
        isSaved = true;

        const newTitle = inputElement.value.trim();

        if (!newTitle || newTitle === originalTitle) {
            titleElement.style.display = 'block';
            inputElement.remove();
            return;
        }

        titleElement.textContent = newTitle;
        titleElement.style.display = 'block';
        inputElement.remove();

        try {
            await fetch('/api/session/rename', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id: id, title: newTitle })
            });
            loadSessions();
        } catch (error) {
            console.error("Gagal mengubah nama sesi:", error);
            titleElement.textContent = originalTitle;
        }
    };

    inputElement.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') saveChanges();
        else if (e.key === 'Escape') {
            isSaved = true;
            titleElement.style.display = 'block';
            inputElement.remove();
        }
    });

    inputElement.addEventListener('blur', () => { saveChanges(); });
}

export async function deleteSession(id, namaChat = "this chat") {
    const konfirmasi = await showDeleteConfirmation(namaChat);
    if (!konfirmasi) return;

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
    } catch (error) { console.error("Gagal menghapus obrolan:", error); }
}

function showDeleteConfirmation(namaChat) {
    return new Promise((resolve) => {
        const modal = document.getElementById('customConfirmModal');
        const messageEl = document.getElementById('confirmMessage');
        const cancelBtn = document.getElementById('confirmCancelBtn');
        const deleteBtn = document.getElementById('confirmDeleteBtn');

        messageEl.innerHTML = `This will delete <strong>${namaChat}</strong>.<br><span style="font-size:0.85rem; opacity:0.6; display:block; margin-top:8px;">Visit <span class="settings-link" style="text-decoration: underline;">settings</span> to delete any memories saved during this chat.</span>`;
        modal.classList.add('active');

        const onDelete = () => { cleanup(); resolve(true); };
        const onCancel = () => { cleanup(); resolve(false); };
        const cleanup = () => {
            modal.classList.remove('active');
            deleteBtn.removeEventListener('click', onDelete);
            cancelBtn.removeEventListener('click', onCancel);
        };

        deleteBtn.addEventListener('click', onDelete);
        cancelBtn.addEventListener('click', onCancel);
    });
}