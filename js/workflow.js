// js/workflow.js
import { showMiniAlert } from './ui.js';

export async function loadWorkflowList() {
    const listEl = document.getElementById('workflowList');
    if (!listEl) return;

    try {
        const res = await fetch('/api/workflows');
        const data = await res.json();

        if (!data.length) {
            listEl.innerHTML = '<div class="no-data-placeholder">Belum ada workflow</div>';
            return;
        }

        listEl.innerHTML = data.map(wf => {
            const config = JSON.parse(wf.trigger_config);
            const jamText = config.time || '-';
            return `
                <div class="workflow-item" data-id="${wf.id}">
                    <div class="workflow-item-info">
                        <strong>${wf.nama}</strong>
                        <span>⏰ ${jamText}${wf.last_run ? ' · terakhir: ' + wf.last_run : ''}</span>
                    </div>
                    <div class="workflow-item-actions">
                        <input type="checkbox" class="workflow-toggle" data-id="${wf.id}" ${wf.enabled ? 'checked' : ''}>
                        <button class="workflow-delete-btn" data-id="${wf.id}" title="Hapus">
                            <i class="fa-solid fa-trash"></i>
                        </button>
                    </div>
                </div>`;
        }).join('');

        listEl.querySelectorAll('.workflow-toggle').forEach(chk => {
            chk.addEventListener('change', async (e) => {
                await toggleWorkflow(e.target.dataset.id, e.target.checked);
            });
        });

        listEl.querySelectorAll('.workflow-delete-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const id = e.currentTarget.dataset.id;
                await deleteWorkflow(id);
            });
        });

    } catch (e) {
        listEl.innerHTML = '<div class="no-data-placeholder">Gagal memuat workflow</div>';
    }
}

export async function createWorkflow(nama, waktu, actionPlugin) {
    if (!nama || !waktu) {
        showMiniAlert('Nama dan waktu wajib diisi');
        return false;
    }

    const actions = actionPlugin ? [{ plugin: actionPlugin, params: {} }] : [];

    try {
        const res = await fetch('/api/workflow/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                nama: nama,
                trigger_type: 'time',
                trigger_config: { time: waktu },
                actions: actions
            })
        });
        const data = await res.json();
        if (data.status === 'success') {
            showMiniAlert('Workflow berhasil dibuat');
            await loadWorkflowList();
            return true;
        } else {
            showMiniAlert('Gagal membuat workflow: ' + (data.message || ''));
            return false;
        }
    } catch (e) {
        showMiniAlert('Gagal terhubung ke server');
        return false;
    }
}

async function toggleWorkflow(id, enabled) {
    try {
        await fetch('/api/workflow/toggle', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id: parseInt(id), enabled: enabled })
        });
    } catch (e) {
        showMiniAlert('Gagal update status workflow');
    }
}

async function deleteWorkflow(id) {
    try {
        await fetch('/api/workflow/delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id: parseInt(id) })
        });
        showMiniAlert('Workflow dihapus');
        await loadWorkflowList();
    } catch (e) {
        showMiniAlert('Gagal menghapus workflow');
    }
}

let lastKnownRuns = {}; // { workflow_id: last_run_value }
let pollingStarted = false;

export function startWorkflowExecutionWatcher() {
    if (pollingStarted) return; // cegah double-start
    pollingStarted = true;

    setInterval(async () => {
        try {
            const res = await fetch('/api/workflows');
            const data = await res.json();

            data.forEach(wf => {
                const prevRun = lastKnownRuns[wf.id];

                // Baru pertama kali kita lihat workflow ini -> simpan aja, jangan notif
                if (prevRun === undefined) {
                    lastKnownRuns[wf.id] = wf.last_run;
                    return;
                }

                // last_run berubah (dan bukan null) -> berarti baru saja dieksekusi
                if (wf.last_run && wf.last_run !== prevRun) {
                    showMiniAlert(`✅ Workflow "${wf.nama}" berhasil dijalankan`);
                    lastKnownRuns[wf.id] = wf.last_run;

                    // Refresh list di modal juga kalau lagi kebuka
                    const modal = document.getElementById('workflowModal');
                    if (modal && modal.classList.contains('active')) {
                        loadWorkflowList();
                    }
                }
            });
        } catch (e) { /* diamkan, jangan ganggu UX kalau server sempat gak respon */ }
    }, 10000); // cek tiap 10 detik
}

// ===== CUSTOM TIME PICKER =====
let selectedHour = null;
let selectedMinute = null;

export function initCustomTimePicker() {
    const wrapper = document.getElementById('customTimePicker');
    const dropdown = document.getElementById('timePickerDropdown');
    const display = document.getElementById('workflowTimeDisplay');
    const hourCol = document.getElementById('hourCol');
    const minuteCol = document.getElementById('minuteCol');

    if (!wrapper || hourCol.dataset.built) return; // cegah re-init
    hourCol.dataset.built = "true";

    for (let h = 0; h < 24; h++) {
        const el = document.createElement('div');
        el.className = 'time-picker-item';
        el.textContent = String(h).padStart(2, '0');
        el.addEventListener('click', () => {
            selectedHour = String(h).padStart(2, '0');
            updateTimeDisplay();
            hourCol.querySelectorAll('.time-picker-item').forEach(i => i.classList.remove('active'));
            el.classList.add('active');
        });
        hourCol.appendChild(el);
    }

    for (let m = 0; m < 60; m += 5) {
        const el = document.createElement('div');
        el.className = 'time-picker-item';
        el.textContent = String(m).padStart(2, '0');
        el.addEventListener('click', () => {
            selectedMinute = String(m).padStart(2, '0');
            updateTimeDisplay();
            minuteCol.querySelectorAll('.time-picker-item').forEach(i => i.classList.remove('active'));
            el.classList.add('active');
        });
        minuteCol.appendChild(el);
    }

    display.addEventListener('click', () => {
        dropdown.classList.toggle('active');
    });

    document.addEventListener('click', (e) => {
        if (!wrapper.contains(e.target)) dropdown.classList.remove('active');
    });
}

function updateTimeDisplay() {
    const display = document.getElementById('workflowTimeDisplay');
    if (selectedHour !== null && selectedMinute !== null) {
        display.value = `${selectedHour}:${selectedMinute}`;
    }
}

export function getSelectedTime() {
    return (selectedHour !== null && selectedMinute !== null) ? `${selectedHour}:${selectedMinute}` : '';
}

export function resetTimePicker() {
    selectedHour = null;
    selectedMinute = null;
    document.getElementById('workflowTimeDisplay').value = '';
    document.querySelectorAll('.time-picker-item').forEach(i => i.classList.remove('active'));
}

// ===== CUSTOM SELECT (Action dropdown) =====
let selectedAction = '';

export function initCustomActionSelect() {
    const trigger = document.getElementById('actionSelectTrigger');
    const options = document.getElementById('actionSelectOptions');
    const label = document.getElementById('actionSelectLabel');
    const wrapper = document.getElementById('customActionSelect');

    if (!trigger || trigger.dataset.built) return;
    trigger.dataset.built = "true";

    trigger.addEventListener('click', () => {
        options.classList.toggle('active');
    });

    options.querySelectorAll('.custom-select-option').forEach(opt => {
        opt.addEventListener('click', () => {
            selectedAction = opt.dataset.value;
            label.textContent = opt.textContent;
            options.querySelectorAll('.custom-select-option').forEach(o => o.classList.remove('active'));
            opt.classList.add('active');
            options.classList.remove('active');
        });
    });

    document.addEventListener('click', (e) => {
        if (!wrapper.contains(e.target)) options.classList.remove('active');
    });
}

export function getSelectedAction() {
    return selectedAction;
}

export function resetActionSelect() {
    selectedAction = '';
    document.getElementById('actionSelectLabel').textContent = '-- Pilih Action --';
    document.querySelectorAll('.custom-select-option').forEach(o => o.classList.remove('active'));
}