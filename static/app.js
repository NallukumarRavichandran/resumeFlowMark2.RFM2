document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('pipelineForm');
  const status = document.getElementById('runStatus');
  const progress = document.getElementById('progress');
  const result = document.getElementById('result');
  const browserPreview = document.getElementById('browserPreview');
  const previewLabel = document.getElementById('previewLabel');
  const previewHint = document.getElementById('previewHint');

  function addProgress(message) {
    const item = document.createElement('div');
    item.className = 'progress-item';
    item.textContent = message;
    progress.appendChild(item);
    progress.scrollTop = progress.scrollHeight;
  }

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const data = new FormData();
    data.append('resume_file', document.getElementById('resumeFile').files[0]);
    data.append('company_name', document.getElementById('companyName').value.trim());
    data.append('job_title', document.getElementById('jobTitle').value.trim());
    data.append('job_description', document.getElementById('jobDescription').value.trim());
    form.querySelector('button').disabled = true;
    progress.replaceChildren();
    result.classList.add('hidden');
    status.textContent = 'Running';
    try {
      const response = await fetch('/api/generate', {method: 'POST', body: data});
      if (!response.ok) throw new Error(`Pipeline returned HTTP ${response.status}`);
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      while (true) {
        const chunk = await reader.read();
        if (chunk.done) break;
        buffer += decoder.decode(chunk.value, {stream: true});
        const events = buffer.split('\n\n');
        buffer = events.pop();
        for (const event of events) {
          if (!event.startsWith('data: ')) continue;
          const payload = JSON.parse(event.slice(6));
          if (payload.error) throw new Error(payload.message);
          addProgress(payload.message);
          if (payload.data?.preview_url) {
            browserPreview.src = `${payload.data.preview_url}?t=${Date.now()}`;
            browserPreview.classList.add('visible');
            previewHint.classList.add('hidden');
            previewLabel.textContent = payload.message;
          }
          if (payload.done && payload.result) {
            const r = payload.result;
            const folder = encodeURIComponent(r.folder_name);
            result.innerHTML = `<strong>Completed</strong><br><span>${r.email}</span><br>` +
              `<a href="/api/download/${folder}/${encodeURIComponent(r.folder_name + '_Tailored_Resume.pdf')}">Download Swooped Resume PDF</a> · ` +
              `<a href="/api/download/${folder}/${encodeURIComponent(r.folder_name + '_Tailored_Resume.docx')}">Download Resume DOCX</a><br>` +
              `<a href="/api/download/${folder}/${encodeURIComponent(r.folder_name + '_Cover_Letter.pdf')}">Download Swooped Cover Letter PDF</a> · ` +
              `<a href="/api/download/${folder}/${encodeURIComponent(r.folder_name + '_Cover_Letter.docx')}">Download Cover Letter DOCX</a>`;
            result.classList.remove('hidden');
          }
        }
      }
      status.textContent = 'Complete';
    } catch (error) {
      addProgress(`Error: ${error.message}`);
      status.textContent = 'Failed';
    } finally {
      form.querySelector('button').disabled = false;
    }
  });
});
