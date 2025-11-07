// src/lib/api.ts
// Centralized API client: warm-up first, then ingest/parse/build with CORS-safe fetch.

const BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/+$/, '');
const KEY = (import.meta.env.VITE_API_KEY || '').trim();

function withCors(init: RequestInit = {}): RequestInit {
  return {
    mode: 'cors',
    credentials: 'omit',
    ...init,
    headers: {
      ...(init.headers || {}),
      ...(KEY ? { Authorization: `Bearer ${KEY}` } : {}),
    },
  };
}

async function sleep(ms: number) {
  return new Promise<void>((res) => setTimeout(res, ms));
}

export async function warmup(): Promise<void> {
  if (!BASE) throw new Error('API base URL missing');
  const url = `${BASE}/health`;

  for (let i = 0; i < 3; i++) {
    const ctl = new AbortController();
    const timeout = setTimeout(() => ctl.abort(), 20000);
    try {
      const r = await fetch(url, withCors({ signal: ctl.signal }));
      clearTimeout(timeout);
      if (r.ok) {
        const j = await r.json().catch(() => ({}));
        if (j?.ok) return; // backend ready
      }
    } catch {
      // retry
    }
    await sleep([500, 1200, 2500][i] || 2500);
  }
  throw new Error('warmup_failed');
}

export async function ingest(file: File): Promise<string> {
  const fd = new FormData();
  fd.append('file', file);
  const r = await fetch(`${BASE}/ingest`, withCors({ method: 'POST', body: fd }));
  if (!r.ok) throw new Error(`ingest ${r.status}`);
  const j = await r.json();
  if (!j?.file_id) throw new Error('ingest: missing file_id');
  return j.file_id as string;
}

export async function parse(file_id: string): Promise<any> {
  const r = await fetch(`${BASE}/parse`, withCors({
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ file_id }),
  }));
  if (!r.ok) throw new Error(`parse ${r.status}`);
  return r.json();
}

export async function build(spec: any): Promise<ArrayBuffer> {
  const r = await fetch(`${BASE}/build`, withCors({
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(spec),
  }));
  if (!r.ok) throw new Error(`build ${r.status}`);
  return r.arrayBuffer();
}
