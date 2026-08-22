const API_BASE = 'http://localhost:8000';

export async function fetchMetrics() {
  const res = await fetch(`${API_BASE}/metrics`);
  if (!res.ok) throw new Error('Failed to fetch metrics');
  return res.json();
}

export async function fetchOrders(flag = null) {
  const url = flag ? `${API_BASE}/orders?flag=${flag}` : `${API_BASE}/orders`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch orders');
  return res.json();
}

export async function scoreOrder(payload) {
  const res = await fetch(`${API_BASE}/score`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error('Failed to score order');
  return res.json();
}

export async function fetchExplain(orderId) {
  const res = await fetch(`${API_BASE}/orders/${orderId}/explain`);
  if (!res.ok) throw new Error('Failed to fetch order explanation');
  return res.json();
}

export async function fetchDriftStatus() {
  const res = await fetch(`${API_BASE}/drift-status`);
  if (!res.ok) throw new Error('Failed to fetch drift status');
  return res.json();
}

export async function submitReview(orderId, decision, note = '') {
  const res = await fetch(`${API_BASE}/orders/${orderId}/review`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ order_id: orderId, decision, note })
  });
  if (!res.ok) throw new Error('Failed to submit analyst review');
  return res.json();
}

export async function fetchAgreementStats() {
  const res = await fetch(`${API_BASE}/agreement-stats`);
  if (!res.ok) throw new Error('Failed to fetch agreement stats');
  return res.json();
}
