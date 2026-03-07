// async function runAnalysis() {
//   const url = document.getElementById('repoUrl').value.trim();
//   const question = document.getElementById('repoQuestion').value.trim();

//   if (!url || !question) {
//     alert('Please enter both a repository URL and a question.');
//     return;
//   }

//   const btn = document.getElementById('analyzeBtn');
//   const resultArea = document.getElementById('resultArea');
//   const resultBox = document.getElementById('resultBox');

//   btn.disabled = true;
//   btn.textContent = 'Analyzing…';
//   resultArea.classList.add('visible');
//   resultBox.innerHTML = `<div class="spinner"><div class="spinner-ring"></div>Analyzing repository…</div>`;
//   resultArea.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

//   try {
//     const response = await fetch('https://api.anthropic.com/v1/messages', {
//       method: 'POST',
//       headers: { 'Content-Type': 'application/json' },
//       body: JSON.stringify({
//         model: 'claude-sonnet-4-20250514',
//         max_tokens: 1000,
//         messages: [{
//           role: 'user',
//           content: `You are an expert software engineering analyst. A user wants to analyze this GitHub repository: ${url}\n\nTheir question: ${question}\n\nProvide a detailed, insightful analysis. If you cannot access the actual repo, give a thoughtful answer based on what can be inferred from the URL and question, and explain what metrics and insights would typically be relevant. Be specific and practical.`
//         }]
//       })
//     });

//     const data = await response.json();
//     const text = (data.content?.map(b => b.text || '').join('') || 'No response received.').trim();
//     const html = text
//       .split(/\n{2,}/)
//       .map(p => `<p style="margin-bottom:12px">${p.replace(/\n/g, '<br/>')}</p>`)
//       .join('');

//     resultBox.innerHTML = `<div class="result-title">Analysis</div>${html}`;
//   } catch (err) {
//     resultBox.innerHTML = `<p style="color:#c0392b">Something went wrong: ${err.message}</p>`;
//   } finally {
//     btn.disabled = false;
//     btn.textContent = 'Analyze →';
//   }
// }
async function runAnalysis() {
  const url = document.getElementById('repoUrl').value.trim();
  const question = document.getElementById('repoQuestion').value.trim();

  if (!url || !question) {
    alert('Please enter both a repository URL and a question.');
    return;
  }

  const btn = document.getElementById('analyzeBtn');
  const resultArea = document.getElementById('resultArea');
  const resultBox = document.getElementById('resultBox');

  btn.disabled = true;
  btn.textContent = 'Analyzing…';

  resultArea.classList.add('visible');
  resultBox.innerHTML = `<div class="spinner"><div class="spinner-ring"></div>Indexing repo…</div>`;

  try {

    // 1️⃣ BUILD INDEX
    await fetch("http://localhost:8000/build-index", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        repo_url: url
      })
    });


    // 2️⃣ ANALYZE QUESTION
    const response = await fetch("http://localhost:8000/analyze", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        question: question
      })
    });

    const data = await response.json();

    const text = data.answer;

    const html = text
      .split(/\n{2,}/)
      .map(p => `<p style="margin-bottom:12px">${p.replace(/\n/g, '<br/>')}</p>`)
      .join('');

    resultBox.innerHTML = `<div class="result-title">Impact Analysis</div>${html}`;

  } catch (err) {

    resultBox.innerHTML = `<p style="color:#c0392b">Error: ${err.message}</p>`;

  } finally {

    btn.disabled = false;
    btn.textContent = 'Analyze →';

  }
}