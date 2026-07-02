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
                <span id="toastMessage">Pesan error di sini</span>
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

export function formatMarkdownToHtml(rawText) {
    if (!rawText) return "";
    return rawText
        .replace(/\[NEWLINE\]/g, "<br>")
        .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
        .replace(/\n/g, "<br>");
}