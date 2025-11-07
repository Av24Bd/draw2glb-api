// src/lib/api.ts
const base = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/+$/, '');
const apiKey = import.meta.env.VITE_API_KEY?.trim();

function url(p: string) {
  const u = `${base}${p}`;
  console.log(`[api] ${u}`);
  return u;
}

function hdrs(json = true): HeadersInit {
  const h: Record<string, string> = {};
  if (json) h['Content-Type'] = 'application/json';
  if (apiKey) h['Authorization'] = `Bearer ${apiKey}`;
  return h;
}

export async function warmup(): Promise<void> {
  console.log('[api] warmup start');
  // Prefer POST /warmup; if server doesn’t have it yet, fall back to /health
  const r = await fetch(url('/warmup'), { method: 'POST', headers: hdrs(false) }).catch(e => {
    console.warn('[api] warmup POST failed, trying /health', e);
    return null;
  });
  if (r && !r.ok) throw new Error(`warmup failed: ${r.status} ${await r.text()}`);
  if (!r) {
    const h = await fetch(url('/health')).catch(e => {
      throw new Error(`health failed: ${e}`);
    });
    if (!h.ok) throw new Error(`health not ok: ${h.status}`);
  }
  console.log('[api] warmup ok');
}

export async function ingest(file: File): Promise<string> {
  const fd = new FormData();
  fd.append('file', file, file.name);
  const r = await fetch(url('/ingest'), { method: 'POST', body: fd, headers: hdrs(false) });
  if (!r.ok) throw new Error(`ingest failed: ${r.status} ${await r.text()}`);
  const j = await r.json();
  console.log('[api] ingest ok', j);
  return j.file_id as string;
}

export async function parse(fileId: string): Promise<any> {
  const r = await fetch(url('/parse'), { method: 'POST', headers: hdrs(true), body: JSON.stringify({ file_id: fileId }) });
  if (!r.ok) throw new Error(`parse failed: ${r.status} ${await r.text()}`);
  const j = await r.json();
  console.log('[api] parse ok', j);
  return j;
}

export async function build(spec: any): Promise<ArrayBuffer> {
  const r = await fetch(url('/build'), { method: 'POST', headers: hdrs(true), body: JSON.stringify(spec) });
  if (!r.ok) throw new Error(`build failed: ${r.status} ${await r.text()}`);
  return await r.arrayBuffer();
}

export function baseUrl() { return base; }
