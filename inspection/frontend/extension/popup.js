document.getElementById('verify-btn').addEventListener('click', async () => {
  const text = document.getElementById('claim-text').value.trim();
  if (!text) return;

  const btn = document.getElementById('verify-btn');
  const resDiv = document.getElementById('result');
  
  btn.textContent = 'Verifying...';
  btn.disabled = true;
  resDiv.style.display = 'none';

  try {
    const response = await fetch('http://127.0.0.1:8000/verify-text', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    });

    if (!response.ok) throw new Error('API Error');
    const data = await response.json();
    
    // UI Updates
    document.getElementById('res-status').textContent = data.status || 'Uncertain';
    document.getElementById('res-conf').textContent = data.confidence || 0;
    document.getElementById('res-summary').textContent = data.summary || 'No summary available.';
    
    resDiv.className = (data.status || 'uncertain').toLowerCase();
    resDiv.style.display = 'block';

  } catch (err) {
    document.getElementById('res-status').textContent = 'Error';
    document.getElementById('res-conf').textContent = '0';
    document.getElementById('res-summary').textContent = 'Could not reach backend API. Make sure it is running heavily.';
    resDiv.className = 'uncertain';
    resDiv.style.display = 'block';
  }

  btn.textContent = 'Verify';
  btn.disabled = false;
});
