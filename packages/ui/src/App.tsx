import React, { useState, useRef, useCallback } from 'react';

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function App() {
  const [file, setFile] = useState<File | null>(null);
  const [dpi, setDpi] = useState(300);
  const [preserveText, setPreserveText] = useState(true);
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleConvert = useCallback(async () => {
    if (!file) return;
    setRunning(true);
    setProgress(0);
    setError(null);

    try {
      const fileData = await file.arrayBuffer();
      const base64 = btoa(String.fromCharCode(...new Uint8Array(fileData)));

      const resp = await fetch('/convert', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          fileData: base64,
          fileName: file.name,
          dpi,
          preserveText,
        }),
      });

      if (!resp.ok) {
        const err = await resp.json();
        throw new Error(err.error || 'Conversion failed');
      }

      const resultHeader = resp.headers.get('X-Result');
      if (resultHeader) {
        const result = JSON.parse(resultHeader);
        setProgress(100);
      }

      const blob = await resp.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = file.name.replace(/\.pdf$/i, '-dark.pdf');
      a.click();
      URL.revokeObjectURL(url);

      setRunning(false);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
      setRunning(false);
    }
  }, [file, dpi, preserveText]);

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <h1 style={styles.title}>PDF Darker</h1>
        <p style={styles.subtitle}>Convert PDF files to dark mode</p>
      </header>

      <main style={styles.main}>
        <section style={styles.card}>
          <h2 style={styles.cardTitle}>File</h2>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            style={styles.fileInput}
          />
          {file && <p style={styles.fileInfo}>{file.name} ({formatBytes(file.size)})</p>}
        </section>

        <section style={styles.card}>
          <h2 style={styles.cardTitle}>Options</h2>
          <div style={styles.field}>
            <label style={styles.label}>DPI</label>
            <select value={dpi} onChange={(e) => setDpi(Number(e.target.value))} style={styles.select}>
              <option value={150}>150 (draft)</option>
              <option value={300}>300 (standard)</option>
              <option value={600}>600 (high quality)</option>
            </select>
          </div>
          <div style={styles.field}>
            <label style={styles.checkboxLabel}>
              <input
                type="checkbox"
                checked={preserveText}
                onChange={(e) => setPreserveText(e.target.checked)}
              />
              Preserve text layer
            </label>
          </div>
        </section>

        <button
          onClick={handleConvert}
          disabled={running || !file}
          style={{
            ...styles.button,
            ...(running || !file ? styles.buttonDisabled : {}),
          }}
        >
          {running ? 'Converting...' : 'Convert to Dark Mode'}
        </button>

        {running && (
          <section style={styles.card}>
            <p>Converting... please wait</p>
          </section>
        )}

        {progress === 100 && (
          <section style={{ ...styles.card, borderColor: '#2ea043' }}>
            <p style={{ color: '#2ea043' }}>Conversion complete! File downloaded.</p>
          </section>
        )}

        {error && (
          <section style={{ ...styles.card, borderColor: '#da3633' }}>
            <p style={{ color: '#da3633' }}>{error}</p>
          </section>
        )}
      </main>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    maxWidth: 640,
    margin: '0 auto',
    padding: '2rem 1rem',
    color: '#c9d1d9',
    background: '#0d1117',
    minHeight: '100vh',
  },
  header: { textAlign: 'center' as const, marginBottom: '2rem' },
  title: { fontSize: '2rem', margin: 0, color: '#58a6ff' },
  subtitle: { margin: '0.5rem 0 0', color: '#8b949e' },
  main: { display: 'flex', flexDirection: 'column' as const, gap: '1rem' },
  card: {
    border: '1px solid #30363d',
    borderRadius: 6,
    padding: '1rem',
    background: '#161b22',
  },
  cardTitle: { margin: '0 0 1rem', fontSize: '1.1rem', color: '#c9d1d9' },
  field: { marginBottom: '0.75rem' },
  label: { display: 'block', marginBottom: '0.25rem', fontSize: '0.875rem', color: '#8b949e' },
  fileInput: { marginBottom: '0.5rem' },
  select: {
    width: '100%',
    padding: '0.5rem',
    border: '1px solid #30363d',
    borderRadius: 4,
    background: '#0d1117',
    color: '#c9d1d9',
    fontSize: '0.875rem',
  },
  checkboxLabel: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    fontSize: '0.875rem',
    color: '#c9d1d9',
  },
  button: {
    padding: '0.75rem 1.5rem',
    border: 'none',
    borderRadius: 6,
    background: '#238636',
    color: '#fff',
    fontSize: '1rem',
    cursor: 'pointer',
    fontWeight: 600,
  },
  buttonDisabled: {
    background: '#21262d',
    color: '#484f58',
    cursor: 'not-allowed',
  },
  fileInfo: { fontSize: '0.875rem', color: '#8b949e' },
};
