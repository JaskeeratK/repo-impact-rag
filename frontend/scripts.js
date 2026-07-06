let indexBuilt = false;
// const API_BASE = "https://verbose-space-engine-69rgg5j44r5rfxr7r-8000.app.github.dev";
const API_BASE = "https://repoimpactanalyzer.vercel.app/"

function renderMarkdown(text) {
  return marked.parse(text);
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
  const retrievalPanel = document.getElementById('retrievalPanel');
  const graphEl = document.getElementById('impactGraph');

  btn.disabled = true;
  btn.textContent = 'Analyzing…';
  resultArea.classList.add('visible');
  document.getElementById('analyze').classList.add('has-results');
  resultBox.innerHTML = `<div class="spinner"><div class="spinner-ring"></div>Analyzing impact…</div>`;
  retrievalPanel.innerHTML = '';
  graphEl.innerHTML = '';

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

    // Render prose answer
    const html = renderMarkdown(data.answer);

    // Affected files
    let filesHtml = '';
    if (data.affected_files && data.affected_files.length > 0) {
      const fileItems = data.affected_files.map(f => `<li>${f}</li>`).join('');
      filesHtml = `
        <div class="affected-files">
          <div class="affected-files-title">🔗 Affected Files</div>
          <ul>${fileItems}</ul>
        </div>
      `;
    }

    resultBox.innerHTML = `
      <div class="result-title">Impact Analysis</div>
      ${html}
      ${filesHtml}
    `;

    // Render impact graph
    if (data.graph) {
      try {
        const g = data.graph;
        const nodeLines = [
          `  A([${g.change.label}<br/><small>${g.change.detail}</small>])`,
          ...g.direct_changes.map((n, i) =>
            `  ${String.fromCharCode(66+i)}[${n.label}<br/><small>${n.file.split('/').pop()}</small>]`),
          ...g.dependencies.map((n, i) =>
            `  ${String.fromCharCode(66+g.direct_changes.length+i)}([${n.label}<br/><small>${n.file.split('/').pop()}</small>])`)
        ];
        const edgeLines = [
          ...g.direct_changes.map((_, i) => `  A --> ${String.fromCharCode(66+i)}`),
          ...g.dependencies.map((_, i) => `  A -.-> ${String.fromCharCode(66+g.direct_changes.length+i)}`)
        ];
        const styleLines = [
          `  style A fill:#FBEAF0,stroke:#993556,color:#4B1528`,
          ...g.direct_changes.map((_, i) =>
            `  style ${String.fromCharCode(66+i)} fill:#FAECE7,stroke:#993C1D,color:#4A1B0C`),
          ...g.dependencies.map((_, i) =>
            `  style ${String.fromCharCode(66+g.direct_changes.length+i)} fill:#FAEEDA,stroke:#854F0B,color:#412402`)
        ];
        const mermaidSrc = `graph TD\n${nodeLines.join('\n')}\n${edgeLines.join('\n')}\n${styleLines.join('\n')}`;

        const div = document.createElement('div');
        div.className = 'mermaid';
        div.textContent = mermaidSrc;
        graphEl.appendChild(div);
        await window.mermaid.run({ nodes: [div] });
      } catch(e) {
        console.error('Graph render failed:', e);
        graphEl.innerHTML = '';
      }
    }

    // Retrieval quality panel (sidebar)
    if (data.chunks && data.chunks.length > 0) {
      const avgScore = (data.chunks.reduce((s, c) => s + c.score, 0) / data.chunks.length).toFixed(2);
      const topScore = Math.max(...data.chunks.map(c => c.score)).toFixed(2);

      const chunkItems = data.chunks.map((chunk) => {
        const pct = Math.round(chunk.score * 100);
        const barColor = chunk.score > 0.75 ? '#2ecc71' : chunk.score > 0.5 ? '#f39c12' : '#e74c3c';
        return `
          <div style="margin-bottom:16px;padding:12px 14px;background:rgba(26,24,20,0.03);border-left:2px solid ${barColor}">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
              <span style="font-size:11px;font-weight:500;letter-spacing:0.08em;text-transform:uppercase;color:var(--text-muted)">${chunk.file}</span>
              <span style="font-size:12px;font-weight:600;color:${barColor}">${pct}%</span>
            </div>
            <div style="height:4px;background:rgba(26,24,20,0.08);border-radius:2px;margin-bottom:10px">
              <div style="height:100%;width:${pct}%;background:${barColor};border-radius:2px;transition:width 0.6s ease"></div>
            </div>
            <pre style="font-size:11px;line-height:1.6;overflow-x:auto;white-space:pre-wrap;word-break:break-word;margin:0;color:var(--text-muted)">${chunk.text.slice(0, 300)}${chunk.text.length > 300 ? '…' : ''}</pre>
          </div>
        `;
      }).join('');

      retrievalPanel.innerHTML = `
        <div style="font-size:11px;font-weight:500;letter-spacing:0.1em;text-transform:uppercase;color:var(--text-muted);margin-bottom:16px">
          🔍 Retrieval Quality — avg <strong>${avgScore}</strong> · top <strong>${topScore}</strong>
        </div>
        ${chunkItems}
      `;
    }

  } catch (err) {
    resultBox.innerHTML = `<p style="color:#c0392b">Error: ${err.message}</p>`;
  } finally {
    btn.disabled = false;
    btn.textContent = 'Analyze →';
  }
}