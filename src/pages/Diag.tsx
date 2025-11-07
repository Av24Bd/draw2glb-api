import React, { useState } from 'react';
import * as api from '@/lib/api';

export default function Diag() {
  const [out, setOut] = useState<string>('Ready');
  const [file, setFile] = useState<File | null>(null);

  async function doWarmup() {
    try {
      setOut('Warming up…');
      await api.warmup();
      setOut('Warmup OK');
    } catch (e: any) {
      setOut(`Warmup ERROR: ${e?.message || e}`);
    }
  }

  async function doIngestParse() {
    if (!file) { setOut('Pick a PDF first'); return; }
    try {
      setOut('Ingesting…');
      const id = await api.ingest(file);
      setOut(`Parsing… (file_id=${id})`);
      const parsed = await api.parse(id);
      setOut(`Parsed OK:\n${JSON.stringify(parsed, null, 2)}`);
    } catch (e: any) {
      setOut(`Ingest/Parse ERROR: ${e?.message || e}`);
    }
  }

  return (
    <div style={{ padding: 16, fontFamily: 'Inter, system-ui, sans-serif' }}>
      <h2>Backend Diagnostics</h2>
      <div>API base: <code>{api.baseUrl() || '(unset)'}</code></div>

      <div style={{ marginTop: 12, display: 'flex', gap: 8 }}>
        <button onClick={doWarmup}>Warmup</button>
        <input type="file" accept=".pdf,.png,.jpg,.jpeg" onChange={e => setFile(e.target.files?.[0] || null)} />
        <button onClick={doIngestParse}>Ingest + Parse</button>
      </div>

      <pre style={{ marginTop: 16, background: '#111', color: '#0f0', padding: 12, whiteSpace: 'pre-wrap' }}>
        {out}
      </pre>
    </div>
  );
}
