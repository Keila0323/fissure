/* ATO Risk Scorer — Frontend Logic */

// ── Theme Toggle ──────────────────────────────────────────
(function () {
  const t = document.querySelector('[data-theme-toggle]');
  const r = document.documentElement;
  let d = matchMedia('(prefers-color-scheme:dark)').matches ? 'dark' : 'light';
  r.setAttribute('data-theme', d);
  updateToggleIcon(t, d);

  t && t.addEventListener('click', () => {
    d = d === 'dark' ? 'light' : 'dark';
    r.setAttribute('data-theme', d);
    updateToggleIcon(t, d);
    t.setAttribute('aria-label', 'Switch to ' + (d === 'dark' ? 'light' : 'dark') + ' mode');
  });

  function updateToggleIcon(btn, theme) {
    if (!btn) return;
    btn.innerHTML = theme === 'dark'
      ? '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>'
      : '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
  }
})();

// ── API Base ───────────────────────────────────────────────
const API_BASE = 'https://ato-risk-scorer.onrender.com';

// ── Character counter ──────────────────────────────────────
const textarea = document.getElementById('flow-input');
const charNum = document.getElementById('char-num');

textarea && textarea.addEventListener('input', () => {
  const count = textarea.value.length;
  charNum.textContent = count;
  charNum.style.color = count > 4800 ? 'var(--color-risk-critical)' : '';
});

// ── Form submission ────────────────────────────────────────
const form = document.getElementById('analyze-form');
const submitBtn = document.getElementById('submit-btn');
const btnText = submitBtn?.querySelector('.btn-text');
const btnLoading = submitBtn?.querySelector('.btn-loading');

form && form.addEventListener('submit', async (e) => {
  e.preventDefault();

  const val = textarea.value.trim();
  if (val.length < 20) {
    showError('Please describe your recovery flow in at least 20 characters.');
    return;
  }

  setLoading(true);
  hideResults();
  hideError();

  try {
    const res = await fetch(`${API_BASE}/api/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ flow_description: val }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Server error (${res.status})`);
    }

    const data = await res.json();
    renderResults(data);
  } catch (err) {
    showError(err.message || 'Analysis failed. Please try again.');
  } finally {
    setLoading(false);
  }
});

function setLoading(on) {
  submitBtn.disabled = on;
  btnText.hidden = on;
  btnLoading.hidden = !on;
}

function hideResults() {
  document.getElementById('results-empty').hidden = false;
  document.getElementById('results-content').hidden = true;
  document.getElementById('results-error').hidden = true;
}

function hideError() {
  document.getElementById('results-error').hidden = true;
}

function showError(msg) {
  document.getElementById('results-empty').hidden = true;
  document.getElementById('results-content').hidden = true;
  const errEl = document.getElementById('results-error');
  document.getElementById('error-message').textContent = msg;
  errEl.hidden = false;
}

// ── Render results ─────────────────────────────────────────
function renderResults(data) {
  document.getElementById('results-empty').hidden = true;
  document.getElementById('results-error').hidden = true;
  const content = document.getElementById('results-content');
  content.hidden = false;

  // Score ring animation
  animateScore(data.risk_score, data.risk_tier);

  // Summary
  document.getElementById('score-summary').textContent = data.summary || '';

  // Lifecycle gaps
  renderLifecycle(data.lifecycle_gaps || {});

  // Vulnerabilities
  renderVulns(data.vulnerabilities || []);

  // Controls
  renderControls(data.controls_summary || []);

  // Scroll to results
  content.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function animateScore(score, tier) {
  const numEl = document.getElementById('score-number');
  const tierEl = document.getElementById('score-tier');
  const arc = document.getElementById('score-arc');

  // Animate number
  let start = 0;
  const duration = 1200;
  const startTime = performance.now();
  function tick(now) {
    const progress = Math.min((now - startTime) / duration, 1);
    const ease = 1 - Math.pow(1 - progress, 3);
    numEl.textContent = Math.round(ease * score);
    if (progress < 1) requestAnimationFrame(tick);
    else numEl.textContent = score;
  }
  requestAnimationFrame(tick);

  // Arc (circumference = 2π × 52 ≈ 327)
  const circumference = 327;
  const filled = (score / 100) * circumference;
  arc.setAttribute('stroke-dasharray', `${filled} ${circumference}`);

  // Tier + color
  const tierLower = (tier || '').toLowerCase();
  let color = 'var(--color-risk-high)';
  if (tierLower === 'critical') color = 'var(--color-risk-critical)';
  else if (tierLower === 'high') color = 'var(--color-risk-high)';
  else if (tierLower === 'moderate') color = 'var(--color-risk-moderate)';
  else if (tierLower === 'low' || tierLower === 'minimal') color = 'var(--color-risk-low)';

  arc.style.setProperty('stroke', color);
  tierEl.textContent = tier ? tier.toUpperCase() + ' RISK' : '—';
  tierEl.className = 'score-tier ' + tierLower;
}

function renderLifecycle(gaps) {
  const grid = document.getElementById('lifecycle-grid');
  const phases = [
    { key: 'onboarding', label: 'Onboarding' },
    { key: 'recovery', label: 'Recovery' },
    { key: 'dormancy', label: 'Dormancy' },
    { key: 'offboarding', label: 'Offboarding' },
  ];

  grid.innerHTML = phases.map(p => {
    const text = gaps[p.key] || 'No data for this phase.';
    return `<div class="lifecycle-item">
      <div class="lifecycle-phase">${esc(p.label)}</div>
      <p class="lifecycle-text">${esc(text)}</p>
    </div>`;
  }).join('');
}

function renderVulns(vulns) {
  const list = document.getElementById('vuln-list');

  list.innerHTML = vulns.map((v, i) => {
    const sevClass = 'sev-' + (v.severity || 'moderate').toLowerCase();
    return `<div class="vuln-card ${sevClass}" data-vuln="${i}">
      <div class="vuln-header" role="button" tabindex="0" aria-expanded="false" aria-controls="vuln-body-${i}">
        <span class="vuln-badge">${esc(v.severity || 'Unknown')}</span>
        <span class="vuln-title">${esc(v.title || 'Vulnerability')}</span>
        <span class="vuln-id">${esc(v.id || '')}</span>
        <svg class="vuln-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" aria-hidden="true">
          <polyline points="6 9 12 15 18 9"/>
        </svg>
      </div>
      <div class="vuln-body" id="vuln-body-${i}">
        ${v.pattern ? `<p class="vuln-pattern">Pattern: ${esc(v.pattern)}</p>` : ''}
        <p>${esc(v.description || '')}</p>
        <p class="vuln-rec-label">Recommendation</p>
        <p class="vuln-rec">${esc(v.recommendation || '')}</p>
      </div>
    </div>`;
  }).join('');

  // Accordion
  list.querySelectorAll('.vuln-header').forEach(header => {
    header.addEventListener('click', () => toggleVuln(header));
    header.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggleVuln(header); }
    });
  });
}

function toggleVuln(header) {
  const card = header.closest('.vuln-card');
  const isOpen = card.classList.contains('open');
  // Close all
  document.querySelectorAll('.vuln-card.open').forEach(c => {
    c.classList.remove('open');
    c.querySelector('.vuln-header').setAttribute('aria-expanded', 'false');
  });
  if (!isOpen) {
    card.classList.add('open');
    header.setAttribute('aria-expanded', 'true');
  }
}

function renderControls(controls) {
  const list = document.getElementById('controls-list');
  list.innerHTML = controls.map(c => `<li>${esc(c)}</li>`).join('');
}

function esc(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}
