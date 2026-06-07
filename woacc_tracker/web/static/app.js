document.addEventListener('click', async (e) => {
  const shareButton = e.target.closest('[data-share-page]');
  if (shareButton) {
    e.preventDefault();
    await shareCurrentPage(shareButton);
    return;
  }

  const row = e.target.closest('tr.clickable');
  if (row && row.dataset.href) window.location.href = row.dataset.href;

  const entry = e.target.closest('tr.entry-row');
  if (entry) {
    const id = entry.dataset.entry;
    const target = document.getElementById('laps-' + id);
    if (target) target.classList.toggle('open');
  }
});

async function shareCurrentPage(button) {
  const url = window.location.href;
  const title = document.title || 'WOACC Tracker';
  const originalText = button.textContent;
  const copiedText = button.dataset.copiedText || 'Copied!';
  const failedText = button.dataset.failedText || 'Copy failed';

  try {
    if (navigator.share) {
      await navigator.share({ title, url });
      return;
    }

    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(url);
      flashButtonText(button, copiedText, originalText);
      return;
    }

    const input = document.createElement('input');
    input.value = url;
    input.setAttribute('readonly', 'readonly');
    input.style.position = 'fixed';
    input.style.left = '-9999px';
    document.body.appendChild(input);
    input.select();
    const ok = document.execCommand('copy');
    document.body.removeChild(input);

    if (ok) {
      flashButtonText(button, copiedText, originalText);
    } else {
      window.prompt('Copy this link', url);
    }
  } catch (err) {
    console.warn('Share failed', err);
    flashButtonText(button, failedText, originalText);
  }
}

function flashButtonText(button, text, originalText) {
  button.textContent = text;
  button.classList.add('copied');
  window.setTimeout(() => {
    button.textContent = originalText;
    button.classList.remove('copied');
  }, 1400);
}

function formatLapTime(ms) {
  if (!ms || ms <= 0) return '—';
  const minutes = Math.floor(ms / 60000);
  const seconds = Math.floor((ms % 60000) / 1000);
  const millis = ms % 1000;
  if (minutes) return `${minutes}:${String(seconds).padStart(2, '0')}.${String(millis).padStart(3, '0')}`;
  return `${seconds}.${String(millis).padStart(3, '0')}`;
}

function formatGap(ms) {
  if (ms === null || ms === undefined || ms === 0) return '—';
  return `+${(ms / 1000).toFixed(3)}`;
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, (char) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  }[char]));
}

function renderLiveLeaderboard(root, data) {
  const body = document.querySelector('[data-live-body]');
  if (!body) return;

  const players = root.querySelector('[data-live-players]');
  if (players) players.textContent = `${root.dataset.playersLabel || 'Player online'}: ${data.status?.players_online || 0}`;

  const opened = new Set([...document.querySelectorAll('.laps-row.open')].map((row) => row.id.replace('laps-', '')));
  const allEntries = data.entries || [];
  const filter = root.dataset.driverFilter || 'all';
  const entries = allEntries.filter((entry) => {
    const state = entry.online_state || (entry.is_online ? 'online' : 'offline');
    if (filter === 'online') return state === 'online';
    if (filter === 'offline') return state === 'offline';
    return true;
  });
  if (!entries.length) {
    const text = allEntries.length
      ? root.dataset.emptyFilter
      : ((data.status?.players_online || 0) <= 0 ? root.dataset.emptyPlayers : root.dataset.emptyLaps);
    body.innerHTML = `<tr><td colspan="10" class="empty">${escapeHtml(text || '')}</td></tr>`;
    return;
  }

  const none = root.dataset.none || '—';
  const lapLabel = root.dataset.lap || 'Lap';
  const timeLabel = root.dataset.time || 'Time';
  const statusLabel = root.dataset.status || 'Status';
  const confirmLabel = root.dataset.confirm || 'Candidate';
  const invalidKnownLabel = root.dataset.invalidKnown || 'Known invalid';
  const onlineLabel = root.dataset.onlineLabel || 'Online';
  const offlineLabel = root.dataset.offlineLabel || 'Offline';
  const unknownLabel = root.dataset.unknownLabel || 'Not confirmed';
  body.innerHTML = entries.map((entry) => {
    const id = escapeHtml(entry.car_id);
    const stateClass = entry.online_state || (entry.is_online ? 'online' : 'offline');
    const stateLabel = stateClass === 'online' ? onlineLabel : (stateClass === 'offline' ? offlineLabel : unknownLabel);
    const lapRows = (entry.laps || []).map((lap) => `
      <tr>
        <td>${lap.lap_number}</td>
        <td>${formatLapTime(lap.lap_time_ms)}</td>
        <td>${escapeHtml(confirmLabel)}</td>
        <td>${formatLapTime(lap.s1_ms)}</td>
        <td>${formatLapTime(lap.s2_ms)}</td>
        <td>${formatLapTime(lap.s3_ms)}</td>
      </tr>
    `).join('');
    return `
      <tr class="entry-row live-entry-row live-driver-${stateClass}" data-entry="${id}" data-driver-online="${stateClass === 'online' ? '1' : '0'}" data-driver-state="${escapeHtml(stateClass)}">
        <td>${entry.position}</td>
        <td><strong>${escapeHtml(entry.driver)}</strong> <span class="driver-state ${stateClass}">${escapeHtml(stateLabel)}</span></td>
        <td>${entry.car ? escapeHtml(entry.car) : escapeHtml(none)}</td>
        <td><strong>${formatLapTime(entry.best_lap_ms)}</strong></td>
        <td>${formatGap(entry.gap_ms)}</td>
        <td>${entry.laps_total} (${entry.laps_candidate})</td>
        <td>${formatLapTime(entry.last_lap_ms)}</td>
        <td>${formatLapTime(entry.last_s1_ms)}</td>
        <td>${formatLapTime(entry.last_s2_ms)}</td>
        <td>${formatLapTime(entry.last_s3_ms)}</td>
      </tr>
      <tr class="laps-row ${opened.has(entry.car_id) ? 'open' : ''}" id="laps-${id}">
        <td colspan="10">
          <div class="laps-box">
            <h3>${escapeHtml(entry.driver)}</h3>
            <table><thead><tr><th>${escapeHtml(lapLabel)}</th><th>${escapeHtml(timeLabel)}</th><th>${escapeHtml(statusLabel)}</th><th>S1</th><th>S2</th><th>S3</th></tr></thead><tbody>${lapRows}</tbody></table>
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

function initLiveLeaderboard() {
  const root = document.querySelector('[data-live-leaderboard]');
  if (!root) return;
  let lastPayload = '';
  let latestData = null;

  root.dataset.driverFilter = root.dataset.driverFilter || 'all';
  document.querySelectorAll('[data-live-driver-filter]').forEach((button) => {
    button.addEventListener('click', () => {
      root.dataset.driverFilter = button.dataset.liveDriverFilter || 'all';
      document.querySelectorAll('[data-live-driver-filter]').forEach((item) => item.classList.toggle('active', item === button));
      if (latestData) renderLiveLeaderboard(root, latestData);
    });
  });

  const refresh = async () => {
    try {
      const response = await fetch(root.dataset.apiUrl, { cache: 'no-store' });
      if (!response.ok) return;
      const data = await response.json();
      const payload = JSON.stringify(data.entries || []) + String(data.status?.players_online || 0);
      latestData = data;
      if (payload === lastPayload) return;
      lastPayload = payload;
      renderLiveLeaderboard(root, data);
    } catch (err) {
      console.warn('Live leaderboard refresh failed', err);
    }
  };
  refresh();
  window.setInterval(refresh, 5000);
}

initLiveLeaderboard();

function renderLiveSummary(root, data) {
  const active = root.querySelector('[data-live-active]');
  const players = root.querySelector('[data-live-players-total]');
  if (active) active.textContent = data.active_count ?? 0;
  if (players) players.textContent = data.players_online ?? 0;
}

function initLiveSummary() {
  const root = document.querySelector('[data-live-summary]');
  if (!root) return;
  let lastPayload = '';
  const refresh = async () => {
    try {
      const response = await fetch(root.dataset.apiUrl, { cache: 'no-store' });
      if (!response.ok) return;
      const data = await response.json();
      const payload = `${data.active_count ?? 0}:${data.players_online ?? 0}`;
      if (payload === lastPayload) return;
      lastPayload = payload;
      renderLiveSummary(root, data);
    } catch (err) {
      console.warn('Live status refresh failed', err);
    }
  };
  refresh();
  window.setInterval(refresh, 5000);
}

initLiveSummary();
