import { useCallback, useEffect, useMemo, useState } from "react";
import "./App.css";

const STORAGE_KEY = "transcripto_user_id";

const apiBase = () =>
  (import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000").replace(/\/$/, "");

type UploadResponse = {
  job_id: string;
  upload_url: string;
  s3_key: string;
  expires_in: number;
};

type StatusResponse = {
  job_id: string;
  user_id: string;
  status: string;
  created_at: string;
  updated_at: string;
  input_s3_path: string | null;
  output_s3_path: string | null;
  transcript_url: string | null;
  error_message: string | null;
  retry_count: number;
};

function randomUserId(): string {
  return `user-${crypto.randomUUID().slice(0, 8)}`;
}

async function readError(res: Response): Promise<string> {
  try {
    const data = await res.json();
    if (typeof data.detail === "string") return data.detail;
    if (Array.isArray(data.detail)) {
      return data.detail.map((d: { msg?: string }) => d.msg ?? JSON.stringify(d)).join("; ");
    }
    return JSON.stringify(data);
  } catch {
    return res.statusText || `HTTP ${res.status}`;
  }
}

export default function App() {
  const [userId, setUserId] = useState(() => {
    try {
      return localStorage.getItem(STORAGE_KEY) ?? randomUserId();
    } catch {
      return randomUserId();
    }
  });

  const [file, setFile] = useState<File | null>(null);
  const [phase, setPhase] = useState<"idle" | "uploading" | "polling">("idle");
  const [jobId, setJobId] = useState<string | null>(null);
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, userId);
    } catch {
      /* ignore */
    }
  }, [userId]);

  const pollMs = 5000;

  useEffect(() => {
    if (!jobId) return;

    let cancelled = false;
    let intervalId: ReturnType<typeof setInterval>;

    const poll = async () => {
      try {
        const res = await fetch(`${apiBase()}/status/${jobId}`);
        if (!res.ok) {
          setError(await readError(res));
          return;
        }
        const data: StatusResponse = await res.json();
        if (cancelled) return;
        setStatus(data);
        setError(null);
        if (data.status === "SUCCESS" || data.status === "FAILED") {
          setPhase("idle");
          clearInterval(intervalId);
        }
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Status request failed");
        }
      }
    };

    void poll();
    intervalId = setInterval(poll, pollMs);
    return () => {
      cancelled = true;
      clearInterval(intervalId);
    };
  }, [jobId]);

  const contentType = useMemo(() => {
    if (!file) return "";
    return file.type || "application/octet-stream";
  }, [file]);

  const busy = phase === "uploading" || phase === "polling";
  const canSubmit = Boolean(file && userId.trim() && !busy);

  const onSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (!file || !userId.trim()) return;

      setError(null);
      setStatus(null);
      setJobId(null);
      setPhase("uploading");

      try {
        const createRes = await fetch(`${apiBase()}/upload`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            user_id: userId.trim(),
            filename: file.name,
            content_type: contentType,
          }),
        });

        if (!createRes.ok) {
          throw new Error(await readError(createRes));
        }

        const created: UploadResponse = await createRes.json();

        const putRes = await fetch(created.upload_url, {
          method: "PUT",
          body: file,
          headers: { "Content-Type": contentType },
        });

        if (!putRes.ok) {
          throw new Error(`Upload to storage failed (${putRes.status})`);
        }

        const confirmUrl = new URL(`${apiBase()}/upload/confirm/${created.job_id}`);
        confirmUrl.searchParams.set("user_id", userId.trim());
        confirmUrl.searchParams.set("s3_key", created.s3_key);

        const confirmRes = await fetch(confirmUrl.toString(), { method: "POST" });
        if (!confirmRes.ok) {
          throw new Error(await readError(confirmRes));
        }

        setPhase("polling");
        setJobId(created.job_id);
      } catch (err) {
        setPhase("idle");
        setError(err instanceof Error ? err.message : "Upload failed");
      }
    },
    [file, userId, contentType]
  );

  const reset = () => {
    setJobId(null);
    setStatus(null);
    setError(null);
    setPhase("idle");
    setFile(null);
  };

  const statusLabel =
    status?.status ??
    (phase === "uploading" ? "…" : phase === "polling" ? "…" : "—");
  const statusClass =
    status?.status === "SUCCESS"
      ? "ok"
      : status?.status === "FAILED"
        ? "bad"
        : status?.status === "PROCESSING"
          ? "run"
          : "pending";

  return (
    <div className="layout">
      <header className="header">
        <h1 className="title">Transcripto</h1>
        <p className="subtitle">Upload audio and track transcription status</p>
      </header>

      <main className="card">
        <form className="form" onSubmit={onSubmit}>
          <label className="field">
            <span className="label">User ID</span>
            <input
              className="input"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              placeholder="your-user-id"
              autoComplete="off"
              disabled={busy}
            />
          </label>

          <label className="field">
            <span className="label">Audio file</span>
            <input
              className="file"
              type="file"
              accept="audio/*,.mp3,.wav,.m4a,.flac,.aac,.ogg"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              disabled={busy}
            />
            {file && (
              <span className="file-meta">
                {file.name} · {(file.size / 1024 / 1024).toFixed(2)} MB
              </span>
            )}
          </label>

          <div className="actions">
            <button type="submit" className="btn primary" disabled={!canSubmit}>
              {phase === "uploading"
                ? "Uploading…"
                : phase === "polling"
                  ? "Processing…"
                  : "Upload & queue"}
            </button>
            <button type="button" className="btn ghost" onClick={reset} disabled={busy}>
              Clear
            </button>
          </div>
        </form>

        {(jobId || status || error) && (
          <section className="status-section" aria-live="polite">
            <h2 className="status-heading">Job</h2>
            {jobId && (
              <p className="mono">
                <span className="muted">job_id</span> {jobId}
              </p>
            )}
            {error && <p className="err">{error}</p>}
            {status && (
              <dl className="dl">
                <div className="dl-row">
                  <dt>Status</dt>
                  <dd>
                    <span className={`pill ${statusClass}`}>{statusLabel}</span>
                  </dd>
                </div>
                <div className="dl-row">
                  <dt>Updated</dt>
                  <dd className="mono small">{status.updated_at}</dd>
                </div>
                {status.input_s3_path && (
                  <div className="dl-row">
                    <dt>Input</dt>
                    <dd className="mono small wrap">{status.input_s3_path}</dd>
                  </div>
                )}
                {status.output_s3_path && (
                  <div className="dl-row">
                    <dt>Output</dt>
                    <dd className="mono small wrap">{status.output_s3_path}</dd>
                  </div>
                )}
                {status.transcript_url && (
                  <div className="dl-row">
                    <dt>Transcript</dt>
                    <dd>
                      <a className="link" href={status.transcript_url} target="_blank" rel="noreferrer">
                        Open link
                      </a>
                    </dd>
                  </div>
                )}
                {status.error_message && (
                  <div className="dl-row">
                    <dt>Error</dt>
                    <dd className="err">{status.error_message}</dd>
                  </div>
                )}
              </dl>
            )}
            {jobId && !error && (
              <p className="hint">
                Polling every {pollMs / 1000}s until the job finishes (SUCCESS or FAILED).
              </p>
            )}
          </section>
        )}
      </main>

      <footer className="footer">
        API: <code className="mono">{apiBase()}</code>
      </footer>
    </div>
  );
}
