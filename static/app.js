document.addEventListener('DOMContentLoaded', () => {
    // Elements
    const dropZone = document.getElementById('dropZone');
    const resumeFileInput = document.getElementById('resumeFileInput');
    const dropZonePrompt = document.getElementById('dropZonePrompt');
    const fileSelectedBadge = document.getElementById('fileSelectedBadge');
    const selectedFileName = document.getElementById('selectedFileName');
    const btnRemoveFile = document.getElementById('btnRemoveFile');

    const generatorForm = document.getElementById('generatorForm');
    const companyNameInput = document.getElementById('companyName');
    const jobTitleInput = document.getElementById('jobTitle');
    const jobDescriptionInput = document.getElementById('jobDescription');
    const btnSubmit = document.getElementById('btnSubmit');
    const btnSpinner = document.getElementById('btnSpinner');

    // Progress Elements
    const progressCard = document.getElementById('progressCard');
    const stepIndicator = document.getElementById('stepIndicator');
    const progressBarFill = document.getElementById('progressBarFill');
    const logText = document.getElementById('logText');

    // Results Elements
    const emptyState = document.getElementById('emptyState');
    const resultsContent = document.getElementById('resultsContent');
    const readyBadge = document.getElementById('readyBadge');
    const displayFolderPath = document.getElementById('displayFolderPath');
    const btnOpenFolder = document.getElementById('btnOpenFolder');
    const resumeDocTitle = document.getElementById('resumeDocTitle');
    const coverDocTitle = document.getElementById('coverDocTitle');
    const btnDownloadResumePdf = document.getElementById('btnDownloadResumePdf');
    const btnDownloadResumeDocx = document.getElementById('btnDownloadResumeDocx');
    const btnDownloadCoverPdf = document.getElementById('btnDownloadCoverPdf');
    const btnDownloadCoverDocx = document.getElementById('btnDownloadCoverDocx');
    const coverLetterPreviewText = document.getElementById('coverLetterPreviewText');

    // Logs Elements
    const btnRefreshLogs = document.getElementById('btnRefreshLogs');
    const logsTableBody = document.getElementById('logsTableBody');

    let currentFolder = '';

    // ==========================================
    // 1. File Upload & Drag-and-Drop Handling
    // ==========================================
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
        });
    });

    dropZone.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            resumeFileInput.files = files;
            updateFileDisplay(files[0].name);
        }
    });

    resumeFileInput.addEventListener('change', () => {
        if (resumeFileInput.files.length > 0) {
            updateFileDisplay(resumeFileInput.files[0].name);
        }
    });

    btnRemoveFile.addEventListener('click', (e) => {
        e.stopPropagation();
        resumeFileInput.value = '';
        fileSelectedBadge.classList.add('hidden');
        dropZonePrompt.classList.remove('hidden');
    });

    function updateFileDisplay(name) {
        selectedFileName.textContent = name;
        dropZonePrompt.classList.add('hidden');
        fileSelectedBadge.classList.remove('hidden');
    }

    // ==========================================
    // 2. Form Submission & SSE Progress Stream
    // ==========================================
    generatorForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        if (!resumeFileInput.files.length) {
            alert('Please select or drop your resume file first.');
            return;
        }

        const formData = new FormData();
        formData.append('resume_file', resumeFileInput.files[0]);
        formData.append('company_name', companyNameInput.value.trim());
        formData.append('job_title', jobTitleInput.value.trim());
        formData.append('job_description', jobDescriptionInput.value.trim());

        // UI State: Running
        setFormSubmitting(true);
        resetTimeline();
        progressCard.classList.remove('hidden');

        try {
            const response = await fetch('/api/generate', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`Server returned error status ${response.status}`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder('utf-8');
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n\n');
                buffer = lines.pop(); // keep last partial chunk

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.substring(6));
                            handleProgressEvent(data);
                        } catch (err) {
                            console.error('Error parsing SSE event:', err, line);
                        }
                    }
                }
            }
        } catch (error) {
            console.error('Generation request failed:', error);
            logText.textContent = `Error: ${error.message}`;
            logText.style.color = '#f87171';
        } finally {
            setFormSubmitting(false);
            loadLogs();
        }
    });

    function handleProgressEvent(evt) {
        if (evt.error) {
            logText.textContent = `Failed: ${evt.message}`;
            logText.style.color = '#f87171';
            return;
        }

        const step = evt.step || 1;
        const total = evt.total || 6;
        const percent = Math.min(100, Math.round((step / total) * 100));

        progressBarFill.style.width = `${percent}%`;
        stepIndicator.textContent = `Step ${step} of ${total}`;
        logText.textContent = evt.message;
        logText.style.color = '#38bdf8';

        // Update timeline step classes
        for (let i = 1; i <= 6; i++) {
            const el = document.getElementById(`step${i}`);
            if (!el) continue;
            if (i < step) {
                el.className = 'timeline-item completed';
            } else if (i === step) {
                el.className = 'timeline-item active';
            } else {
                el.className = 'timeline-item';
            }
        }

        // On complete
        if (evt.done && evt.result) {
            markTimelineComplete();
            displayResults(evt.result);
        } else if (evt.data && evt.data.folder_name) {
            displayResults(evt.data);
        }
    }

    function resetTimeline() {
        progressBarFill.style.width = '10%';
        stepIndicator.textContent = 'Step 1 of 6';
        logText.textContent = 'Connecting to Swooped.co engine...';
        logText.style.color = '#38bdf8';
        for (let i = 1; i <= 6; i++) {
            const el = document.getElementById(`step${i}`);
            if (el) el.className = 'timeline-item' + (i === 1 ? ' active' : '');
        }
    }

    function markTimelineComplete() {
        progressBarFill.style.width = '100%';
        stepIndicator.textContent = 'Completed';
        for (let i = 1; i <= 6; i++) {
            const el = document.getElementById(`step${i}`);
            if (el) el.className = 'timeline-item completed';
        }
    }

    // Credentials Elements
    const displayCredEmail = document.getElementById('displayCredEmail');
    const displayCredPass = document.getElementById('displayCredPass');
    const btnCopyEmail = document.getElementById('btnCopyEmail');
    const btnCopyPass = document.getElementById('btnCopyPass');
    const btnDeleteSwooped = document.getElementById('btnDeleteSwooped');
    const deleteBtnText = document.getElementById('deleteBtnText');

    let currentFolder = '';
    let activeRunId = '';

    // Clipboard copy buttons
    btnCopyEmail.addEventListener('click', () => {
        navigator.clipboard.writeText(displayCredEmail.textContent);
        btnCopyEmail.textContent = 'Copied!';
        setTimeout(() => { btnCopyEmail.textContent = 'Copy'; }, 1500);
    });

    btnCopyPass.addEventListener('click', () => {
        navigator.clipboard.writeText(displayCredPass.textContent);
        btnCopyPass.textContent = 'Copied!';
        setTimeout(() => { btnCopyPass.textContent = 'Copy'; }, 1500);
    });

    // Delete Account button in results card
    btnDeleteSwooped.addEventListener('click', async () => {
        if (!activeRunId) return;
        if (!confirm('Are you sure you want to permanently delete this account and all its data from Swooped.co?')) return;

        deleteBtnText.textContent = 'Deleting...';
        btnDeleteSwooped.disabled = true;

        const formData = new FormData();
        formData.append('account_id', activeRunId);

        try {
            const resp = await fetch('/api/delete-account', {
                method: 'POST',
                body: formData
            });
            const data = await resp.json();
            if (data.success) {
                deleteBtnText.textContent = '✓ Account Deleted on Swooped';
                btnDeleteSwooped.className = 'btn-delete-swooped deleted';
                loadLogs();
            } else {
                alert('Deletion failed: ' + (data.error || 'Unknown error'));
                deleteBtnText.textContent = 'Delete Account on Swooped';
                btnDeleteSwooped.disabled = false;
            }
        } catch (e) {
            console.error('Delete request failed:', e);
            alert('Failed to connect to server for deletion.');
            deleteBtnText.textContent = 'Delete Account on Swooped';
            btnDeleteSwooped.disabled = false;
        }
    });

    function displayResults(data) {
        emptyState.classList.add('hidden');
        resultsContent.classList.remove('hidden');
        readyBadge.textContent = 'Ready (Saved to Disk)';
        readyBadge.className = 'badge-ready success';

        currentFolder = data.folder_name || '';
        activeRunId = data.run_id || '';
        displayFolderPath.textContent = `downloads/${currentFolder}/`;

        resumeDocTitle.textContent = `${currentFolder}_Tailored_Resume`;
        coverDocTitle.textContent = `${currentFolder}_Cover_Letter`;

        btnDownloadResumePdf.href = `/api/download/${currentFolder}/${currentFolder}_Tailored_Resume.pdf`;
        btnDownloadResumeDocx.href = `/api/download/${currentFolder}/${currentFolder}_Tailored_Resume.docx`;
        btnDownloadCoverPdf.href = `/api/download/${currentFolder}/${currentFolder}_Cover_Letter.pdf`;
        btnDownloadCoverDocx.href = `/api/download/${currentFolder}/${currentFolder}_Cover_Letter.docx`;

        // Display credentials
        if (data.email) displayCredEmail.textContent = data.email;
        if (data.password) displayCredPass.textContent = data.password;

        btnDeleteSwooped.disabled = false;
        btnDeleteSwooped.className = 'btn-delete-swooped';
        deleteBtnText.textContent = 'Delete Account on Swooped';

        if (data.cover_letter_text) {
            coverLetterPreviewText.textContent = data.cover_letter_text;
        }
    }

    btnOpenFolder.addEventListener('click', async () => {
        if (!currentFolder) return;
        const formData = new FormData();
        formData.append('folder_name', currentFolder);
        try {
            await fetch('/api/open-folder', {
                method: 'POST',
                body: formData
            });
        } catch (e) {
            console.error('Could not trigger open folder:', e);
        }
    });

    function setFormSubmitting(isSubmitting) {
        btnSubmit.disabled = isSubmitting;
        if (isSubmitting) {
            btnSpinner.classList.remove('hidden');
        } else {
            btnSpinner.classList.add('hidden');
        }
    }

    // ==========================================
    // 3. Account Lifecycle Logs & History Table
    // ==========================================
    async function loadLogs() {
        try {
            const res = await fetch('/api/logs');
            if (!res.ok) return;
            const logs = await res.json();
            renderLogsTable(logs);
        } catch (e) {
            console.error('Failed to load logs:', e);
        }
    }

    function renderLogsTable(logs) {
        if (!logs || logs.length === 0) {
            logsTableBody.innerHTML = '<tr><td colspan="6" class="table-empty">No account generation logs recorded yet.</td></tr>';
            return;
        }

        logsTableBody.innerHTML = logs.map(item => {
            const isDeleted = item.deleted || item.status === 'Deleted on Swooped';
            const statusClass = isDeleted ? 'status-deleted' : (item.status.includes('Failed') ? 'status-failed' : 'status-working');
            const statusLabel = isDeleted ? '✓ Wiped on Swooped' : item.status;
            const cleanFolder = (item.folder_path ? item.folder_path.split(/[\\/]/).pop() : '') || `${item.company_name}_${item.job_title}`.replace(/ /g, '_');

            const deleteActionHtml = isDeleted ? 
                `<span class="status-badge status-deleted">✓ Wiped</span>` :
                `<button type="button" class="btn-table-action btn-table-delete" onclick="triggerAccountDelete('${item.id}')">Delete on Swooped</button>`;

            return `
                <tr>
                    <td style="color: #94a3b8; font-size: 0.8rem;">${item.created_at || 'Just now'}</td>
                    <td>
                        <div class="temp-email-cell">${item.email || 'Generating...'}</div>
                        ${item.password ? `<div style="font-size: 0.72rem; color: #94a3b8; margin-top: 2px;">Pass: <code style="color: #cbd5e1;">${item.password}</code></div>` : ''}
                    </td>
                    <td>
                        <strong style="color: #fff;">${item.company_name || '—'}</strong>
                        <div style="font-size: 0.75rem; color: #94a3b8;">${item.job_title || '—'}</div>
                    </td>
                    <td>
                        <div class="action-links-group">
                            <a href="/api/download/${cleanFolder}/${cleanFolder}_Tailored_Resume.pdf" class="btn-table-action" title="Download Resume PDF">Resume PDF</a>
                            <a href="/api/download/${cleanFolder}/${cleanFolder}_Tailored_Resume.docx" class="btn-table-action" title="Download Resume Word">Resume DOCX</a>
                            <a href="/api/download/${cleanFolder}/${cleanFolder}_Cover_Letter.pdf" class="btn-table-action" title="Download Cover Letter PDF">Cover PDF</a>
                            <a href="/api/download/${cleanFolder}/${cleanFolder}_Cover_Letter.docx" class="btn-table-action" title="Download Cover Letter Word">Cover DOCX</a>
                        </div>
                    </td>
                    <td>
                        <span class="status-badge ${statusClass}">${statusLabel}</span>
                    </td>
                    <td>
                        <div style="display: flex; gap: 6px;">
                            <button type="button" class="btn-table-action" onclick="triggerFolderOpen('${cleanFolder}')">Folder</button>
                            ${deleteActionHtml}
                        </div>
                    </td>
                </tr>
            `;
        }).join('');
    }

    window.triggerAccountDelete = async (runId) => {
        if (!confirm('Permanently delete this account from Swooped.co?')) return;
        const formData = new FormData();
        formData.append('account_id', runId);
        try {
            const resp = await fetch('/api/delete-account', {
                method: 'POST',
                body: formData
            });
            const data = await resp.json();
            if (data.success) {
                loadLogs();
            } else {
                alert('Deletion failed: ' + (data.error || 'Unknown error'));
            }
        } catch (e) {
            console.error('Delete failed:', e);
            alert('Could not connect to delete account.');
        }
    };

    window.triggerFolderOpen = async (folderName) => {
        const formData = new FormData();
        formData.append('folder_name', folderName);
        try {
            await fetch('/api/open-folder', {
                method: 'POST',
                body: formData
            });
        } catch (e) {
            console.error('Could not open folder:', e);
        }
    };

    btnRefreshLogs.addEventListener('click', loadLogs);

    // Initial load
    loadLogs();
});
