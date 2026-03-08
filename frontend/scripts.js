let indexBuilt = false;
const API_BASE = "https://miniature-fortnight-pj64w4ppp9939q7-8000.app.github.dev/";
async function buildIndex() {
  const url = document.getElementById('repoUrl').value.trim();
  if (!url) { alert('Please enter a repository URL.'); return; }

  const btn = document.getElementById('buildBtn');
  const statusBox = document.getElementById('indexStatus');

  btn.disabled = true;
  btn.textContent = 'Building…';
  statusBox.innerHTML = `<div class="spinner"><div class="spinner-ring"></div>Cloning and indexing repo…</div>`;

  try {
    const response = await fetch("https://miniature-fortnight-pj64w4ppp9939q7-8000.app.github.dev/build-index", {
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
    const response = await fetch("https://miniature-fortnight-pj64w4ppp9939q7-8000.app.github.dev/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question })
    });

    const data = await response.json();

    if (data.status !== "success") {
      resultBox.innerHTML = `<p style="color:#c0392b">❌ ${data.message}</p>`;
      return;
    }

    // Format answer
    const html = data.answer
      .split(/\n{2,}/)
      .map(p => `<p style="margin-bottom:12px">${p.replace(/\n/g, '<br/>')}</p>`)
      .join('');

    // Format affected files
    let filesHtml = '';
    if (data.affected_files && data.affected_files.length > 0) {
      const fileItems = data.affected_files
        .map(f => `<li style="font-family:monospace;font-size:13px;margin-bottom:4px">${f}</li>`)
        .join('');
      filesHtml = `
        <div class="result-title" style="margin-top:24px">🔗 Affected Files</div>
        <ul style="padding-left:20px;margin-top:8px">${fileItems}</ul>
      `;
    }

    resultBox.innerHTML = `
      <div class="result-title">Impact Analysis</div>
      ${html}
      ${filesHtml}
    `;

  } catch (err) {
    resultBox.innerHTML = `<p style="color:#c0392b">Error: ${err.message}</p>`;
  } finally {
    btn.disabled = false;
    btn.textContent = 'Analyze →';
  }
}