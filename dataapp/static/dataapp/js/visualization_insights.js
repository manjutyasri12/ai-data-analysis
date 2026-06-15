document.addEventListener('click', function (e) {
  const btn = e.target.closest('[data-explain-with-gemini]');
  if (!btn) return;

  const chartId = btn.getAttribute('data-chart-id');
  const payloadEl = document.getElementById(`chart-payload-${chartId}`);
  if (!payloadEl) return;

  let payload = {};
  try {
    payload = JSON.parse(payloadEl.value || payloadEl.textContent || '{}');
  } catch (err) {
    payload = {};
  }

  const outEl = document.getElementById(`gemini-explain-${chartId}`);
  if (outEl) {
    outEl.innerHTML = '<div class="small text-secondary">Explaining with Gemini...</div>';
  }

  const csrfToken = (document.querySelector('[name=csrfmiddlewaretoken]') || {}).value;

  fetch('/ai/explain/chart/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrfToken || '',
    },
    body: JSON.stringify(payload),
  })
    .then((r) => r.json().then((j) => ({ ok: r.ok, json: j })))
    .then(({ ok, json }) => {
      if (!outEl) return;
      if (ok && json && json.success) {
        outEl.innerHTML = '<div class="small" style="white-space:pre-wrap;">' + (json.answer || '') + '</div>';
      } else {
        const msg = (json && (json.error || json.response)) ? (json.error || json.response) : 'Gemini explanation failed.';
        outEl.innerHTML = '<div class="small text-danger" style="white-space:pre-wrap;">' + msg + '</div>';
      }
    })
    .catch((err) => {
      if (!outEl) return;
      outEl.innerHTML = '<div class="small text-danger">Request failed. ' + err + '</div>';
    });
});

