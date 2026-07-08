// js/ui.js
let toastTimeout;

export function injectModalsAndToasts() {
    const modalHTML = `
        <div id="customPromptModal" class="modal-overlay">
            <div class="modal-box">
                <div class="modal-preview-side">
                    <img id="customPromptPreview" src="" alt="Preview">
                </div>
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

        <div id="customConfirmModal" class="confirm-overlay">
            <div class="confirm-box">
                <h3>Delete chat?</h3>
                <p id="confirmMessage">This will delete <strong>Chat Name</strong>.</p>
                <div class="confirm-buttons">
                    <button id="confirmCancelBtn" class="btn-confirm-cancel">Cancel</button>
                    <button id="confirmDeleteBtn" class="btn-confirm-delete">Delete</button>
                </div>
            </div>
        </div>`;
    document.body.insertAdjacentHTML('beforeend', modalHTML);

    const inputWrapper = document.querySelector('.input-wrapper');
    if (inputWrapper) {
        const toastHTML = `
            <div id="miniAlertToast" class="toast-container">
                <i class="fa-solid fa-triangle-exclamation"></i>
                <span id="toastMessage">This is a mini alert message.</span>
            </div>`;
        inputWrapper.insertAdjacentHTML('afterbegin', toastHTML);
    }
}

export function showMiniAlert(message) {
    const toast = document.getElementById('miniAlertToast');
    const toastMsg = document.getElementById('toastMessage');
    
    if (!toast || !toastMsg) {
        alert(message);
        return;
    }

    clearTimeout(toastTimeout);
    toastMsg.textContent = message;
    toast.classList.add('show');

    toastTimeout = setTimeout(() => {
        toast.classList.remove('show');
    }, 3500);
}

export function autoGrow(element) {
    element.style.height = "5px";
    element.style.height = (element.scrollHeight) + "px";
}

export function formatMarkdownToHtml(text) {
    if (!text) return "";

    const codeBlockRegex = /```(\w*)\n([\s\S]*?)(```|$)/g;
    const savedBlocks = [];

    // 1. Ekstrak semua code block dulu, ganti sementara jadi placeholder
    let processedText = text.replace(codeBlockRegex, (match, language, code) => {
        const lang = language || 'txt';

        // Trim baris kosong di awal/akhir saja, isi tengah tetap utuh
        const trimmedCode = code.replace(/^\n+/, '').replace(/\n+$/, '');

        const cleanCode = trimmedCode
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");

        const safeCode = btoa(unescape(encodeURIComponent(trimmedCode)));

        const blockHtml = `
            <div class="minimal-code-wrapper">
                <div class="minimal-code-header">
                    <span class="minimal-code-lang">${lang.toLowerCase()}</span>
                    <button class="minimal-code-copy-btn" data-code="${safeCode}" onclick="window.copyMinimalCode(this)" title="Copy code">
                        <svg class="copy-icon" viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
                            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                        </svg>
                        <svg class="check-icon hidden" viewBox="0 0 24 24" width="16" height="16" stroke="#4cd137" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
                            <polyline points="20 6 9 17 4 12"></polyline>
                        </svg>
                    </button>
                </div>
                <pre class="language-${lang.toLowerCase()}"><code class="language-${lang.toLowerCase()}">${cleanCode}</code></pre>
            </div>
        `;

        savedBlocks.push(blockHtml);
        return `\u0000BLOCK${savedBlocks.length - 1}\u0000`;
    });

    // 2. Baru proses inline-code, aman karena code block sudah "diamankan" jadi placeholder
    processedText = processedText.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');
    processedText = processedText.replace(/\*\*([^\*]+)\*\*/g, '<strong>$1</strong>');

    // 3. Kembalikan code block asli menggantikan placeholder
    processedText = processedText.replace(/\u0000BLOCK(\d+)\u0000/g, (match, index) => {
        return savedBlocks[parseInt(index, 10)];
    });

    return processedText;
}