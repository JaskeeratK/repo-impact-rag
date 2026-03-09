(function () {
  const canvas = document.getElementById('ria-net');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  const COLS = 9, ROWS = 9;
  const GH_LABELS = [
    'main', 'feat/auth', 'fix/deps', '@octocat', '@dev-maria',
    'react', 'lodash', '#1042', 'ci/cd', 'tests',
    'v2.4.1', 'webpack', 'release', 'prettier', 'jest',
    'origin/HEAD', 'eslint', 'hotfix/xss', '#987', '@torvalds'
  ];

  let nodes = [], edges = [], pulses = [], nodeGrid = [];
  let CW = 0, CH = 0; // canvas pixel size

  function resize() {
    const rect = canvas.getBoundingClientRect();
    CW = canvas.width  = Math.round(rect.width);
    CH = canvas.height = Math.round(rect.height);
  }

  function getZone() {
    // Circle centred in canvas, with equal margin top/bottom/left/right
    const margin = Math.min(CW, CH) * 0.13;
    const r = Math.min(CW, CH) / 2 - margin;
    return { cx: CW / 2, cy: CH / 2, r: Math.max(r, 40) };
  }

  function clearLabels() {
    nodes.forEach(n => { if (n._lbl) { n._lbl.remove(); n._lbl = null; } });
  }

  function init() {
    clearLabels();
    nodes = []; edges = []; pulses = []; nodeGrid = [];

    const z = getZone();
    const cellW = (z.r * 2) / (COLS - 1);
    const cellH = (z.r * 2) / (ROWS - 1);
    const startX = z.cx - z.r;
    const startY = z.cy - z.r;

    // Build grid, masking nodes outside circle
    let seq = 0;
    for (let r = 0; r < ROWS; r++) {
      nodeGrid[r] = [];
      for (let c = 0; c < COLS; c++) {
        const nx = (c / (COLS - 1)) * 2 - 1;  // -1 to 1
        const ny = (r / (ROWS - 1)) * 2 - 1;
        const dist = Math.sqrt(nx * nx + ny * ny);
        if (dist > 1.02) { nodeGrid[r][c] = null; seq++; continue; }

        const jx = (Math.random() - 0.5) * cellW * 0.28;
        const jy = (Math.random() - 0.5) * cellH * 0.28;
        const isHub = (r % 3 === 1 && c % 3 === 1 && dist < 0.82);
        const isMid = (r + c) % 3 === 1;
        const fade  = Math.max(0, 1 - dist);

        const node = {
          id:    seq++,
          x:     startX + c * cellW + jx,
          y:     startY + r * cellH + jy,
          r:     (isHub ? 5 : isMid ? 2.8 : 1.4) * (0.4 + fade * 0.6),
          alpha: 0.28 + fade * 0.72,
          isHub,
          glow:  0,
          label: GH_LABELS[seq % GH_LABELS.length],
          showLabel:  false,
          labelTimer: 80 + Math.random() * 260,
          _lbl: null,
        };
        nodeGrid[r][c] = node;
        nodes.push(node);
      }
    }

    // Re-number ids sequentially
    nodes.forEach((n, i) => { n.id = i; });
    let ri = 0;
    for (let r = 0; r < ROWS; r++)
      for (let c = 0; c < COLS; c++)
        if (nodeGrid[r][c]) nodeGrid[r][c].id = ri++;

    // Edges
    const get = (r, c) => (r >= 0 && r < ROWS && c >= 0 && c < COLS) ? nodeGrid[r][c] : null;
    for (let r = 0; r < ROWS; r++) {
      for (let c = 0; c < COLS; c++) {
        const a = get(r, c); if (!a) continue;
        const R  = get(r,     c + 1);
        const D  = get(r + 1, c);
        const DR = get(r + 1, c + 1);
        const DL = get(r + 1, c - 1);
        if (R)                    edges.push([a.id, R.id]);
        if (D)                    edges.push([a.id, D.id]);
        if (DR && (r+c)%2===0)    edges.push([a.id, DR.id]);
        if (DL && (r+c)%2===1)    edges.push([a.id, DL.id]);
      }
    }

    // Floating labels for hub nodes
    nodes.filter(n => n.isHub).forEach(n => {
      const el = document.createElement('div');
      el.style.cssText = [
        'position:fixed',
        'font-family:Inter,sans-serif',
        'font-size:10px',
        'font-weight:400',
        'letter-spacing:0.07em',
        'color:#8B4513',
        'background:rgba(240,232,216,0.85)',
        'backdrop-filter:blur(4px)',
        '-webkit-backdrop-filter:blur(4px)',
        'border:1px solid rgba(139,69,19,0.18)',
        'border-radius:5px',
        'padding:3px 8px',
        'pointer-events:none',
        'white-space:nowrap',
        'opacity:0',
        'transition:opacity 0.45s ease',
        'z-index:20',
      ].join(';');
      el.textContent = n.label;
      document.body.appendChild(el);
      n._lbl = el;
    });
  }

  function spawnPulse() {
    if (!nodes.length) return;
    const hubs = nodes.filter(n => n.isHub);
    if (!hubs.length) return;
    const src = hubs[Math.floor(Math.random() * hubs.length)];
    src.glow = 0.6;
    edges
      .filter(([a, b]) => a === src.id || b === src.id)
      .forEach(([a, b]) => {
        pulses.push({ from: a===src.id?a:b, to: a===src.id?b:a, t:0, speed: 0.007+Math.random()*0.007 });
      });
  }

  function draw() {
    requestAnimationFrame(draw);
    if (!CW || !CH) return;
    ctx.clearRect(0, 0, CW, CH);

    // Glow decay
    nodes.forEach(n => { if (n.glow > 0) n.glow = Math.max(0, n.glow - 0.009); });

    // Advance pulses + propagate
    const done = [];
    pulses.forEach((p, pi) => {
      p.t += p.speed;
      if (p.t >= 1) {
        const dest = nodes[p.to];
        if (dest) {
          dest.glow = Math.min(1, dest.glow + 0.9);
          if (Math.random() < 0.28) {
            edges
              .filter(([a,b]) => (a===dest.id||b===dest.id) && a!==p.from && b!==p.from)
              .slice(0, 1)
              .forEach(([a,b]) => {
                if (pulses.length < 15)
                  pulses.push({ from:dest.id, to:a===dest.id?b:a, t:0, speed:0.007+Math.random()*0.007 });
              });
          }
        }
        done.push(pi);
      }
    });
    done.reverse().forEach(pi => pulses.splice(pi, 1));

    // Edges
    edges.forEach(([a, b]) => {
      const na = nodes[a], nb = nodes[b];
      if (!na || !nb) return;
      const lit = Math.max(na.glow, nb.glow);
      const ea  = Math.min(na.alpha, nb.alpha);
      ctx.beginPath();
      ctx.moveTo(na.x, na.y);
      ctx.lineTo(nb.x, nb.y);
      ctx.strokeStyle = `rgba(125,62,16,${(0.12 + lit*0.28) * ea})`;
      ctx.lineWidth = 0.6 + lit * 0.65;
      ctx.stroke();
    });

    // Travelling pulse dots
    pulses.forEach(p => {
      const na = nodes[p.from], nb = nodes[p.to];
      if (!na || !nb) return;
      const px = na.x + (nb.x - na.x) * p.t;
      const py = na.y + (nb.y - na.y) * p.t;
      const g = ctx.createRadialGradient(px, py, 0, px, py, 8);
      g.addColorStop(0, 'rgba(195,105,25,0.7)');
      g.addColorStop(1, 'rgba(195,105,25,0)');
      ctx.beginPath(); ctx.arc(px, py, 8, 0, Math.PI*2); ctx.fillStyle=g; ctx.fill();
      ctx.beginPath(); ctx.arc(px, py, 2, 0, Math.PI*2); ctx.fillStyle='#bf6318'; ctx.fill();
    });

    // Nodes
    nodes.forEach(n => {
      const { glow, alpha: a } = n;
      if (glow > 0.02) {
        const gr = n.r * (2.5 + glow * 5);
        const g = ctx.createRadialGradient(n.x, n.y, n.r*0.2, n.x, n.y, gr);
        g.addColorStop(0, `rgba(200,105,25,${glow*0.48*a})`);
        g.addColorStop(1, 'rgba(200,105,25,0)');
        ctx.beginPath(); ctx.arc(n.x, n.y, gr, 0, Math.PI*2); ctx.fillStyle=g; ctx.fill();
      }
      const r = n.r + glow * 1.6;
      ctx.beginPath(); ctx.arc(n.x, n.y, r, 0, Math.PI*2);
      ctx.fillStyle = glow > 0.05
        ? `rgba(${175+Math.round(glow*55)},${72+Math.round(glow*18)},18,${a})`
        : n.isHub
          ? `rgba(112,56,14,${0.82*a})`
          : `rgba(148,90,42,${0.50*a})`;
      ctx.fill();
    });

    // Floating labels — convert canvas coords to screen coords
    const rect = canvas.getBoundingClientRect();
    const sx = rect.width  / CW;
    const sy = rect.height / CH;
    nodes.filter(n => n.isHub && n._lbl).forEach(n => {
      const el = n._lbl;
      n.labelTimer--;
      if (n.labelTimer <= 0) {
        n.showLabel = !n.showLabel;
        n.labelTimer = n.showLabel ? 160+Math.random()*200 : 90+Math.random()*130;
        el.style.opacity = n.showLabel ? '1' : '0';
      }
      if (n.glow > 0.45) el.style.opacity = '1';
      else if (!n.showLabel) el.style.opacity = '0';
      el.style.left = (rect.left + (n.x + n.r + 6) * sx) + 'px';
      el.style.top  = (rect.top  + (n.y - 9)       * sy) + 'px';
    });
  }

  // Defer init until the browser has laid out the page so getBoundingClientRect has real values
  function boot() {
    resize();
    if (CW < 10 || CH < 10) {
      // layout not ready yet, try again next frame
      requestAnimationFrame(boot);
      return;
    }
    init();
    setTimeout(spawnPulse, 1100);
    setTimeout(spawnPulse, 1500);
    setTimeout(spawnPulse, 2000);
    setInterval(spawnPulse, 3000);
    draw();
  }

  window.addEventListener('resize', () => { resize(); init(); });
  // Wait for fonts + layout
  if (document.readyState === 'complete') {
    requestAnimationFrame(boot);
  } else {
    window.addEventListener('load', () => requestAnimationFrame(boot));
  }
})();