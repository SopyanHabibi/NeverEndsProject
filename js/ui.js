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
        document.body.insertAdjacentHTML('beforeend', toastHTML); // <-- ganti dari inputWrapper ke document.body
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

function renderMathSafely(latex, displayMode) {
    if (!window.katex) return latex; // fallback kalau KaTex belum load
    try {
        return katex.renderToString(latex, {
            throwOnError: false,
            displayMode: displayMode
        });
    } catch (error) {
        return latex; // fallback ke raw text kalau LaTex nya invalid
    }
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


    // 1.5. BARU: Ekstrak block math \[ ... \]
    processedText = processedText.replace(/\\\[([\s\S]*?)\\\]/g, (match, latex) => {
        const html = renderMathSafely(latex.trim(), true);
        savedBlocks.push(`<div class="math-block">${html}</div>`);
        return `\u0000BLOCK${savedBlocks.length - 1}\u0000`;
    });

    // 1.6. BARU: Ekstrak inline math \( ... \)
    processedText = processedText.replace(/\\\(([\s\S]*?)\\\)/g, (match, latex) => {
        const html = renderMathSafely(latex.trim(), false);
        savedBlocks.push(`<span class="math-inline">${html}</span>`);
        return `\u0000BLOCK${savedBlocks.length - 1}\u0000`;
    });

    // 2. Inline-code & bold (SAMA SEPERTI SEBELUMNYA)
    processedText = processedText.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');
    processedText = processedText.replace(/\*\*([^\*]+)\*\*/g, '<strong>$1</strong>');

    // 3. Restore semua placeholder (code block + math, sama-sama pakai mekanisme ini)
    processedText = processedText.replace(/\u0000BLOCK(\d+)\u0000/g, (match, index) => {
        return savedBlocks[parseInt(index, 10)];
    });

    // 4. BARU: rapiin baris kosong berlebih (biar teks-ke-code gak kejauhan jaraknya)
    // Maksimal 1 baris kosong (2x \n) di mana pun di teks
    processedText = processedText.replace(/\n{3,}/g, '\n\n');
    // Khusus di sekitar code block: hilangin baris kosong yang nempel langsung ke wrapper
    processedText = processedText.replace(/\n+(\s*<div class="minimal-code-wrapper">)/g, '$1');
    processedText = processedText.replace(/(<\/div>\s*)\n+/g, '$1');

    return processedText;
}

// Fungsi global buat tombol copy code - dipanggil lewat onclick di HTML
window.copyMinimalCode = function(buttonElement) {
    const encodedCode = buttonElement.getAttribute('data-code');
    const originalCode = decodeURIComponent(escape(atob(encodedCode)));

    navigator.clipboard.writeText(originalCode).then(() => {
        const copyIcon = buttonElement.querySelector('.copy-icon');
        const checkIcon = buttonElement.querySelector('.check-icon');

        copyIcon.classList.add('hidden');
        checkIcon.classList.remove('hidden');


        setTimeout(() => {
            copyIcon.classList.remove('hidden');
            checkIcon.classList.add('hidden');
        }, 1500);
    }).catch(err => {
        console.log('Gagal copy code:', err);
    });
};