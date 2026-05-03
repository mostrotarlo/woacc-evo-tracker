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
