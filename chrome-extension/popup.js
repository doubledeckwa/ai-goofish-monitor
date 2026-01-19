// Popup script for the Chrome extension
document.addEventListener('DOMContentLoaded', function() {
  const extractBtn = document.getElementById('extractBtn');
  const copyBtn = document.getElementById('copyBtn');
  const stateOutput = document.getElementById('stateOutput');
  const statusDiv = document.getElementById('status');

  let latestSnapshot = null;

  function setLoading(isLoading) {
    extractBtn.disabled = isLoading;
    extractBtn.textContent = isLoading ? 'Collecting, please wait....' : '1.Click to get the environment+Login status';
  }

  function updateStatus(message, isSuccess = false) {
    statusDiv.textContent = message;
    statusDiv.className = 'status ' + (isSuccess ? 'success' : 'error');
    setTimeout(() => {
      statusDiv.textContent = '';
      statusDiv.className = 'status';
    }, 4000);
  }

  function renderSnapshot(snapshot) {
    latestSnapshot = snapshot;
    stateOutput.value = JSON.stringify(snapshot, null, 2);
  }

  async function captureSnapshot() {
    setLoading(true);
    updateStatus('Collecting browser environment and login status...');
    stateOutput.value = '';

    chrome.runtime.sendMessage({ type: 'captureSnapshot' }, (response) => {
      setLoading(false);

      if (chrome.runtime.lastError) {
        updateStatus('Communication failed: ' + chrome.runtime.lastError.message);
        return;
      }
      if (!response || !response.ok) {
        updateStatus('Collection failed: ' + (response?.error || 'unknown error'));
        return;
      }

      renderSnapshot(response.data);
      updateStatus('Collection completed, generatedJSON', true);
    });
  }

  function copySnapshot() {
    if (!stateOutput.value) {
      updateStatus('No data to copy');
      return;
    }
    navigator.clipboard.writeText(stateOutput.value)
      .then(() => updateStatus('Copied to clipboard', true))
      .catch(err => updateStatus('Copy failed: ' + err));
  }

  extractBtn.addEventListener('click', captureSnapshot);
  copyBtn.addEventListener('click', copySnapshot);
});
