/**
 * ResumeFlow Mark 2 — Client Automation Controller
 * Atelier Noir Visual System & Real-Time Telemetry Stream
 */

document.addEventListener('DOMContentLoaded', () => {
  // DOM Element References
  const form = document.getElementById('pipelineForm');
  const submitBtn = document.getElementById('submitBtn');
  const submitBtnText = document.getElementById('submitBtnText');
  const formStatusBadge = document.getElementById('formStatusBadge');
  const systemStatusLabel = document.getElementById('systemStatusLabel');
  const runStatus = document.getElementById('runStatus');

  // Dropzone & File Input Elements
  const dropzone = document.getElementById('dropzone');
  const resumeFileInput = document.getElementById('resumeFile');
  const fileSelectedBadge = document.getElementById('fileSelectedBadge');
  const fileExtTag = document.getElementById('fileExtTag');
  const fileNameDisplay = document.getElementById('fileNameDisplay');
  const removeFileBtn = document.getElementById('removeFileBtn');

  // Input Fields & Character Counter
  const companyInput = document.getElementById('companyName');
  const jobTitleInput = document.getElementById('jobTitle');
  const jobDescInput = document.getElementById('jobDescription');
  const charCount = document.getElementById('charCount');

  // Viewport & Terminal Elements
  const browserPreview = document.getElementById('browserPreview');
  const viewportEmptyState = document.getElementById('viewportEmptyState');
  const previewLabel = document.getElementById('previewLabel');
  const terminalLogs = document.getElementById('terminalLogs');
  const terminalStepTracker = document.getElementById('terminalStepTracker');

  // Results Suite
  const resultsSuite = document.getElementById('resultsSuite');
  const generatedEmailBadge = document.getElementById('generatedEmailBadge');
  const downloadResumePdf = document.getElementById('downloadResumePdf');
  const downloadResumeDocx = document.getElementById('downloadResumeDocx');
  const downloadCoverPdf = document.getElementById('downloadCoverPdf');
  const downloadCoverDocx = document.getElementById('downloadCoverDocx');

  // Thinking Orb Canvases & Controllers
  const topbarOrbCanvas = document.getElementById('topbarOrb');
  const submitBtnOrbCanvas = document.getElementById('submitBtnOrb');
  const viewportOrbCanvas = document.getElementById('viewportOrb');
  const viewportOrbState = document.getElementById('viewportOrbState');

  let topbarOrb = null;
  let submitBtnOrb = null;
  let viewportOrb = null;

  if (typeof window.createThinkingOrb === 'function') {
    if (topbarOrbCanvas) {
      topbarOrb = window.createThinkingOrb(topbarOrbCanvas, {
        state: 'breathing',
        size: 20,
        dark: true,
        speed: 1
      });
    }
    if (submitBtnOrbCanvas) {
      submitBtnOrb = window.createThinkingOrb(submitBtnOrbCanvas, {
        state: 'working',
        size: 20,
        dark: false,
        speed: 1.2,
        paused: true
      });
    }
    if (viewportOrbCanvas) {
      viewportOrb = window.createThinkingOrb(viewportOrbCanvas, {
        state: 'searching',
        size: 64,
        dark: true,
        speed: 1
      });
    }
  }

  // Stepper Elements
  const stepNodes = [
    document.getElementById('step-node-1'),
    document.getElementById('step-node-2'),
    document.getElementById('step-node-3'),
    document.getElementById('step-node-4'),
    document.getElementById('step-node-5'),
  ];
  const stepConnectors = [
    document.getElementById('step-conn-1'),
    document.getElementById('step-conn-2'),
    document.getElementById('step-conn-3'),
    document.getElementById('step-conn-4'),
  ];

  // --------------------------------------------------------------------------
  // File Dropzone Handling
  // --------------------------------------------------------------------------
  function handleFileSelected(file) {
    if (!file) return;
    const name = file.name;
    const ext = name.split('.').pop().toUpperCase();
    fileExtTag.textContent = ext;
    fileNameDisplay.textContent = `${name} (${(file.size / 1024).toFixed(0)} KB)`;
    dropzone.style.display = 'none';
    fileSelectedBadge.classList.add('active');
  }

  function clearSelectedFile() {
    resumeFileInput.value = '';
    fileSelectedBadge.classList.remove('active');
    dropzone.style.display = 'flex';
  }

  resumeFileInput.addEventListener('change', (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelected(e.target.files[0]);
    }
  });

  removeFileBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    clearSelectedFile();
  });

  ['dragenter', 'dragover'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.add('drag-over');
    });
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove('drag-over');
    });
  });

  dropzone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files && files.length > 0) {
      resumeFileInput.files = files;
      handleFileSelected(files[0]);
    }
  });

  // Character Counter
  jobDescInput.addEventListener('input', () => {
    const length = jobDescInput.value.length;
    charCount.textContent = `${length.toLocaleString()} chars`;
  });

  // --------------------------------------------------------------------------
  // Telemetry & Stepper Helpers
  // --------------------------------------------------------------------------
  function getTimestamp() {
    const now = new Date();
    return `[${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}]`;
  }

  function logTerminal(message, type = 'normal') {
    const entry = document.createElement('div');
    entry.className = 'terminal-entry';

    const timestamp = document.createElement('span');
    timestamp.className = 'terminal-timestamp';
    timestamp.textContent = getTimestamp();

    const msg = document.createElement('span');
    msg.className = `terminal-msg ${type}`;
    msg.textContent = message;

    entry.appendChild(timestamp);
    entry.appendChild(msg);
    terminalLogs.appendChild(entry);
    terminalLogs.scrollTop = terminalLogs.scrollHeight;
  }

  function updateStepper(stepIndex) {
    // stepIndex: 1 to 5
    stepNodes.forEach((node, idx) => {
      const stepNum = idx + 1;
      node.classList.remove('active', 'completed');
      if (stepNum < stepIndex) {
        node.classList.add('completed');
      } else if (stepNum === stepIndex) {
        node.classList.add('active');
      }
    });

    stepConnectors.forEach((conn, idx) => {
      if (idx + 1 < stepIndex) {
        conn.classList.add('active');
      } else {
        conn.classList.remove('active');
      }
    });
  }

  function resolveStepStage(step, total, message) {
    const lower = (message || '').toLowerCase();
    if (lower.includes('account') || lower.includes('signup') || lower.includes('sign up') || lower.includes('temporary email')) {
      return 1;
    }
    if (lower.includes('upload') || lower.includes('parse') || lower.includes('base resume')) {
      return 2;
    }
    if (lower.includes('job') || lower.includes('targeting') || lower.includes('company') || lower.includes('role')) {
      return 3;
    }
    if (lower.includes('tailor') || lower.includes('generate') || lower.includes('synthesiz') || lower.includes('ai')) {
      return 4;
    }
    if (lower.includes('download') || lower.includes('convert') || lower.includes('complet') || lower.includes('deliver')) {
      return 5;
    }
    if (total > 0) {
      const ratio = step / total;
      if (ratio < 0.25) return 1;
      if (ratio < 0.45) return 2;
      if (ratio < 0.7) return 3;
      if (ratio < 0.9) return 4;
      return 5;
    }
    return 1;
  }

  // --------------------------------------------------------------------------
  // Form Submission & SSE Pipeline Processing
  // --------------------------------------------------------------------------
  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const file = resumeFileInput.files[0];
    if (!file) {
      logTerminal('Error: Please select or drop a valid resume file before launching.', 'error');
      return;
    }

    const company = companyInput.value.trim();
    const role = jobTitleInput.value.trim();
    const jobDesc = jobDescInput.value.trim();

    if (!company || !role || !jobDesc) {
      logTerminal('Error: Company name, target role, and job description are required.', 'error');
      return;
    }

    // Prepare Multipart Data
    const formData = new FormData();
    formData.append('resume_file', file);
    formData.append('company_name', company);
    formData.append('job_title', role);
    formData.append('job_description', jobDesc);

    // UI State: Running
    submitBtn.disabled = true;
    submitBtn.classList.add('loading');
    submitBtnText.textContent = 'Pipeline Active...';
    formStatusBadge.textContent = 'RUNNING';
    systemStatusLabel.textContent = 'Pipeline Running';
    runStatus.textContent = 'RUNNING';

    // Thinking Orb activations
    if (submitBtnOrb) {
      submitBtnOrbCanvas.style.display = 'inline-block';
      submitBtnOrb.resume();
      submitBtnOrb.setState('working');
    }
    if (topbarOrb) {
      topbarOrb.setState('listening');
    }
    if (viewportOrb) {
      viewportOrb.setState('connecting');
      if (viewportOrbState) viewportOrbState.textContent = 'STATE: CONNECTING';
    }

    resultsSuite.classList.remove('visible');
    terminalLogs.replaceChildren();
    logTerminal(`Pipeline initiated for ${role} at ${company}.`, 'highlight');
    updateStepper(1);

    try {
      const response = await fetch('/api/generate', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Pipeline API request failed with HTTP status ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split('\n\n');
        buffer = events.pop();

        for (const event of events) {
          if (!event.startsWith('data: ')) continue;
          const jsonStr = event.slice(6).trim();
          if (!jsonStr) continue;

          const payload = JSON.parse(jsonStr);

          if (payload.error) {
            throw new Error(payload.message || 'An unexpected error occurred in browser automation');
          }

          // Update Terminal Log
          const stepText = payload.step && payload.total ? `[Step ${payload.step}/${payload.total}] ` : '';
          logTerminal(`${stepText}${payload.message}`);

          if (payload.step && payload.total) {
            terminalStepTracker.textContent = `Step ${payload.step} / ${payload.total}`;
            const stage = resolveStepStage(payload.step, payload.total, payload.message);
            updateStepper(stage);

            if (viewportOrb) {
              const orbStates = {
                1: 'connecting',
                2: 'searching',
                3: 'solving',
                4: 'weaving',
                5: 'composing'
              };
              const nextState = orbStates[stage] || 'working';
              viewportOrb.setState(nextState);
              if (viewportOrbState) viewportOrbState.textContent = `STATE: ${nextState.toUpperCase()}`;
            }
          }

          // Live Browser Viewport Preview
          if (payload.data?.preview_url) {
            browserPreview.src = `${payload.data.preview_url}?t=${Date.now()}`;
            browserPreview.classList.add('visible');
            viewportEmptyState.style.display = 'none';
            previewLabel.textContent = payload.message;
          }

          // Pipeline Completion
          if (payload.done && payload.result) {
            const res = payload.result;
            const folder = encodeURIComponent(res.folder_name);
            const prefix = encodeURIComponent(res.folder_name);

            downloadResumePdf.href = `/api/download/${folder}/${prefix}_Tailored_Resume.pdf`;
            downloadResumeDocx.href = `/api/download/${folder}/${prefix}_Tailored_Resume.docx`;
            downloadCoverPdf.href = `/api/download/${folder}/${prefix}_Cover_Letter.pdf`;
            downloadCoverDocx.href = `/api/download/${folder}/${prefix}_Cover_Letter.docx`;

            if (res.email) {
              generatedEmailBadge.textContent = res.email;
            }

            resultsSuite.classList.add('visible');
            updateStepper(5);
            stepNodes[4].classList.add('completed');
            if (viewportOrb) {
              viewportOrb.setState('shaping');
              if (viewportOrbState) viewportOrbState.textContent = 'STATE: SHAPING';
            }
            logTerminal('Automation successfully completed. Tailored documents ready for export.', 'highlight');
          }
        }
      }

      runStatus.textContent = 'COMPLETED';
      formStatusBadge.textContent = 'COMPLETED';
      systemStatusLabel.textContent = 'System Ready';
    } catch (err) {
      logTerminal(`Automation Failure: ${err.message}`, 'error');
      runStatus.textContent = 'FAILED';
      formStatusBadge.textContent = 'ERROR';
      systemStatusLabel.textContent = 'Pipeline Fault';
    } finally {
      submitBtn.disabled = false;
      submitBtn.classList.remove('loading');
      submitBtnText.textContent = 'Launch Swooped Pipeline';
      if (submitBtnOrb) {
        submitBtnOrb.pause();
        submitBtnOrbCanvas.style.display = 'none';
      }
      if (topbarOrb) {
        topbarOrb.setState('breathing');
      }
    }
  });
});
