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