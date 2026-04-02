let indexBuilt = false;
const API_BASE = "https://miniature-fortnight-pj64w4ppp9939q7-8000.app.github.dev";

function renderMarkdown(text) {
  return text
    .replace(/^### (.+)$/gm, '<h4 style="font-family:Fraunces,serif;font-weight:400;margin:16px 0 8px">$1</h4>')
    .replace(/^## (.+)$/gm, '<h3 style="font-family:Fraunces,serif;font-weight:400;margin:20px 0 8px">$1</h3>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/`([^`]+)`/g, '<code style="background:rgba(139,69,19,0.08);padding:2px 6px;border-radius:3px;font-size:12px">$1</code>')
    .replace(/^\* (.+)$/gm, '<li style="margin-bottom:6px">$1</li>')
    .replace(/^- (.+)$/gm, '<li style="margin-bottom:6px">$1</li>')
    .replace(/^\d+\. (.+)$/gm, '<li style="margin-bottom:6px">$1</li>')
    .replace(/(<li[^>]*>.*<\/li>\n?)+/g, m => `<ul style="padding-left:20px;margin:8px 0">${m}</ul>`)
    .replace(/\n{2,}/g, '</p><p style="margin-bottom:12px">')
    .replace(/\n/g, '<br/>');
}

async function buildIndex() {
  const url = document.getElementById('repoUrl').value.trim();
  if (!url) { alert('Please enter a repository URL.'); return; }

  const btn = document.getElementById('buildBtn');
  const statusBox = document.getElementById('indexStatus');

  btn.disabled = true;
  btn.textContent = 'Building…';
  statusBox.innerHTML = `<div class="spinner"><div class="spinner-ring"></div>Cloning and indexing repo…</div>`;

  try {
    const response = await fetch(`${API_BASE}/build-index`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ repo_url: url })
    });

    const data = await response.json();

    if (data.status === "success") {
      indexBuilt = true;
      statusBox.innerHTML = `<p style="color:#2ecc71">✅ Index built — ${data.files_indexed} files indexed.</p>`;
      document.getElementById('questionSection').style.display = 'block';
    } else {
      statusBox.innerHTML = `<p style="color:#c0392b">❌ ${data.message}</p>`;
    }
  } catch (err) {
    statusBox.innerHTML = `<p style="color:#c0392b">Error: ${err.message}</p>`;
  } finally {
    btn.disabled = false;
    btn.textContent = 'Build Index';
  }
}

async function runAnalysis() {
  if (!indexBuilt) { alert('Please build the index first.'); return; }

  const question = document.getElementById('repoQuestion').value.trim();
  if (!question) { alert('Please enter a question.'); return; }

  const btn = document.getElementById('analyzeBtn');
  const resultArea = document.getElementById('resultArea');
  const resultBox = document.getElementById('resultBox');

  btn.disabled = true;
  btn.textContent = 'Analyzing…';
  resultArea.classList.add('visible');
  resultBox.innerHTML = `<div class="spinner"><div class="spinner-ring"></div>Analyzing impact…</div>`;

  try {
    const response = await fetch(`${API_BASE}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question })
    });

    const data = await response.json();

    if (data.status !== "success") {
      resultBox.innerHTML = `<p style="color:#c0392b">❌ ${data.message}</p>`;
      return;
    }

    // Render answer
    const html = `<p style="margin-bottom:12px">${renderMarkdown(data.answer)}</p>`;

    // Affected files
    let filesHtml = '';
    if (data.affected_files && data.affected_files.length > 0) {
      const fileItems = data.affected_files
        .map(f => `<li>${f}</li>`)
        .join('');
      filesHtml = `
        <div class="affected-files">
          <div class="affected-files-title">🔗 Affected Files</div>
          <ul>${fileItems}</ul>
        </div>
      `;
    }

    // Collapsible debug context
    let contextHtml = '';
    if (data.contexts && data.contexts.length > 0) {
      const contextItems = data.contexts.map((ctx, i) => `
        <div style="margin-bottom:16px">
          <div style="font-size:11px;font-weight:500;letter-spacing:0.1em;
                      text-transform:uppercase;color:var(--text-muted);
                      margin-bottom:6px">Context ${i + 1}</div>
          <pre style="background:rgba(26,24,20,0.04);border-left:2px solid #8B4513;
                      padding:12px 16px;font-size:12px;line-height:1.6;
                      overflow-x:auto;white-space:pre-wrap;
                      word-break:break-word;margin:0">${ctx}</pre>
        </div>
      `).join('');

      contextHtml = `
        <div style="margin-top:24px;padding-top:20px;
                    border-top:1px solid rgba(26,24,20,0.08)">
          <details>
            <summary style="cursor:pointer;font-size:12px;font-weight:500;
                            letter-spacing:0.1em;text-transform:uppercase;
                            color:var(--text-muted);margin-bottom:16px">
              🔍 Retrieved Context (Debug)
            </summary>
            <div style="margin-top:12px">${contextItems}</div>
          </details>
        </div>
      `;
    }

    resultBox.innerHTML = `
      <div class="result-title">Impact Analysis</div>
      ${html}
      ${filesHtml}
      ${contextHtml}
    `;

  } catch (err) {
    resultBox.innerHTML = `<p style="color:#c0392b">Error: ${err.message}</p>`;
  } finally {
    btn.disabled = false;
    btn.textContent = 'Analyze →';
  }
}