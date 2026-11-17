"use client";

import { useEffect, useState } from "react";
import { isAxiosError } from "axios";
import { api } from "@/lib/api";

type Clip = {
  id: string;
  kind: "progress" | "demonstration";
  duration: number;
  createdAt: string;
  canDelete: boolean;
  feedback?: string;
  allowAi?: boolean;
  aiStatus?: "not_requested" | "processing" | "complete" | "failed";
  aiError?: string;
  transcript?: string;
  summary?: string;
};

export default function ProgressVideos({ studentId, activityId, role }: {
  studentId: string;
  activityId: string;
  role: "parent" | "therapist";
}) {
  const path = `/api/progress-videos/${encodeURIComponent(studentId)}/${encodeURIComponent(activityId)}`;
  const [clips, setClips] = useState<Clip[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [file, setFile] = useState<File>();
  const [consent, setConsent] = useState(false);
  const [videoUrls, setVideoUrls] = useState<Record<string, string>>({});
  const [feedback, setFeedback] = useState<Record<string, string>>({});
  const [loaded, setLoaded] = useState(false);
  const load = async () => {
    setClips((await api.get<Clip[]>(path)).data);
    setLoaded(true);
  };
  const run = async (action: () => Promise<void>) => {
    setBusy(true);
    setError("");
    try {
      await action();
    } catch (e) {
      const detail: unknown = isAxiosError(e) ? e.response?.data?.detail : undefined;
      if (typeof detail === "string") {
        setError(detail);
      } else if (isAxiosError(e) && e.response) {
        setError(e.response.status >= 500
          ? `The video service had a server error (${e.response.status}). Please try again.`
          : `The request could not be completed (${e.response.status}). Check your access and try again.`);
      } else {
        setError("Could not reach the video service. Check that the backend is running, then retry.");
      }
    } finally {
      setBusy(false);
    }
  };
  useEffect(() => {
    if (loaded || busy) return;
    void run(load);
  // The list is loaded once when this activity's video panel appears.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [studentId, activityId]);

  useEffect(() => {
    if (!loaded) return;
    let cancelled = false;
    const resolveVideos = async () => {
      const missing = clips.filter(clip => !videoUrls[clip.id]);
      if (!missing.length) return;
      const urls = await Promise.all(missing.map(async clip => {
        try {
          const { data } = await api.get<{ url: string }>(`${path}/${clip.id}/play`);
          return [clip.id, data.url] as const;
        } catch {
          return [clip.id, ""] as const;
        }
      }));
      if (!cancelled) setVideoUrls(current => ({ ...current, ...Object.fromEntries(urls) }));
    };
    void resolveVideos();
    const timer = setInterval(() => {
      void api.get<Clip[]>(path).then(({ data }) => {
        setClips(data);
        setError(current => current === "Could not reach the video service. Check that the backend is running, then retry." ? "" : current);
      }).catch(() => undefined);
    }, 8000);
    return () => { cancelled = true; clearInterval(timer); };
  }, [loaded, clips, videoUrls, path]);

  return (
    <section aria-labelledby={`activity-videos-${activityId}`} style={{ marginTop: 14, padding: 20, borderRadius: 16, background: "rgba(255,255,255,.82)", border: "1px solid var(--border, rgba(100,116,139,.2))", boxShadow: "0 8px 24px rgba(39,54,83,.06)" }}>
          <div style={{ marginBottom: 18 }}>
            <h3 id={`activity-videos-${activityId}`} style={{ margin: "0 0 5px", fontSize: 19, color: "var(--primary-dark)", fontWeight: 750 }}>Progress videos</h3>
            <p style={{ margin: 0, color: "var(--muted, #64748b)", fontSize: 14, lineHeight: 1.5 }}>
              Share and review private videos for this activity. Only the linked family and assigned therapist can view them.
            </p>
          </div>
          <form style={{ marginBottom: 20, padding: 18, borderRadius: 14, background: "linear-gradient(135deg, rgba(236,242,250,.92), rgba(246,242,249,.94))", border: "1px solid rgba(93,112,146,.18)" }} onSubmit={e => {
            e.preventDefault();
            const form = e.currentTarget;
            if (!file) return;
            if (file.size > 250 * 1024 * 1024) {
              setError("Choose a video under 250 MB. It will be compressed before private storage.");
              return;
            }
            void run(async () => {
              await api.post(path, file, {
                params: { allow_ai: consent },
                headers: { "Content-Type": "application/octet-stream" },
                timeout: 360_000,
              });
              form.reset();
              setFile(undefined);
              setConsent(false);
              setVideoUrls({});
              await load();
            });
          }}>
            <h4 style={{ margin: "0 0 4px", color: "var(--primary-dark)", fontSize: 16 }}>{role === "parent" ? "Share a practice video" : "Upload a therapist demonstration"}</h4>
            <p style={{ margin: "0 0 14px", color: "var(--muted, #64748b)", fontSize: 13 }}>Choose a video up to 3 minutes and 250 MB. It will be compressed and stored privately.</p>
            <label style={{ display: "block", padding: 14, borderRadius: 11, background: "rgba(255,255,255,.82)", border: "1px dashed rgba(65,86,119,.4)", color: "var(--primary-dark)", fontWeight: 650 }}>
              <span style={{ display: "block", marginBottom: 8 }}>Select a video file</span>
              <input style={{ display: "block", maxWidth: "100%", fontWeight: 400 }} type="file" accept="video/mp4,video/quicktime,video/webm,video/x-msvideo" disabled={busy}
                onChange={e => setFile(e.target.files?.[0])} />
              {file && <span style={{ display: "block", marginTop: 8, fontWeight: 500, fontSize: 13, color: "var(--muted, #64748b)" }}>{file.name} · {(file.size / (1024 * 1024)).toFixed(1)} MB</span>}
            </label>
            {role === "parent" && (
              <label style={{ display: "flex", alignItems: "flex-start", gap: 8, margin: "12px 0", fontSize: 13, lineHeight: 1.45 }}>
                <input type="checkbox" checked={consent} disabled={busy} onChange={e => setConsent(e.target.checked)} />
                <span>Allow Google Gemini to transcribe this video and create an AI summary for the therapist.</span>
              </label>
            )}
            <button type="submit" className="btn-primary" style={{ marginTop: 14, padding: "11px 18px" }} disabled={busy || !file}>{busy ? "Compressing and uploading…" : role === "parent" ? consent ? "Upload and create AI summary" : "Upload practice video" : "Upload demonstration"}</button>
          </form>
          <h4 style={{ margin: "0 0 10px", color: "var(--primary-dark)", fontSize: 16 }}>Shared videos</h4>
          {error && <div role="alert" style={{ marginBottom: 12, padding: "10px 12px", borderRadius: 10, color: "#991b1b", background: "#fef2f2", border: "1px solid #fecaca" }}>{error}</div>}
          {busy && <p role="status" style={{ color: "var(--muted, #64748b)" }}>Please wait…</p>}
          {!loaded && !busy && <button type="button" className="btn-secondary" onClick={() => void run(load)}>Retry loading videos</button>}
          {loaded && clips.length === 0 && <p style={{ margin: 0, padding: 14, borderRadius: 10, background: "rgba(241,245,249,.8)", color: "#475569" }}>No videos shared yet. Your uploaded videos will appear here.</p>}
          {clips.map(clip => (
            <article key={clip.id} style={{ display: "grid", gridTemplateColumns: "minmax(240px, 1.15fr) minmax(240px, 1fr)", gap: 16, padding: 16, marginTop: 10, borderRadius: 13, border: "1px solid var(--border, rgba(100,116,139,.2))", background: "rgba(255,255,255,.75)" }}>
              <div>
              <strong style={{ display: "block", color: "var(--primary-dark)", fontSize: 16 }}>{clip.kind === "progress" ? "Progress clip" : "Therapist demonstration"}</strong>
              <p style={{ margin: "5px 0 12px", color: "var(--muted, #64748b)", fontSize: 13 }}>{new Date(clip.createdAt).toLocaleString()} · {clip.duration} seconds</p>
              {clip.canDelete && (
                <button className="btn-secondary" type="button" disabled={busy} onClick={() => {
                  if (!window.confirm("Delete this video permanently?")) return;
                  void run(async () => {
                    await api.delete(`${path}/${clip.id}`);
                    setVideoUrls({});
                    await load();
                  });
                }}>Delete</button>
              )}
              {clip.feedback && <p style={{ whiteSpace: "pre-wrap" }}>Therapist feedback: {clip.feedback}</p>}
              {role === "therapist" && clip.kind === "progress" && (
                <div>
                  {clip.summary && <div style={{ marginTop: 10, padding: 12, borderRadius: 10, background: "rgba(224,242,254,.75)" }}>
                    <strong>AI summary for therapist review</strong>
                    <p style={{ whiteSpace: "pre-wrap", marginBottom: 0 }}>{clip.summary}</p>
                  </div>}
                  {clip.transcript && <details style={{ marginTop: 8 }}>
                    <summary style={{ cursor: "pointer", fontWeight: 600 }}>View generated transcript</summary>
                    <p style={{ whiteSpace: "pre-wrap", maxHeight: 260, overflowY: "auto" }}>{clip.transcript}</p>
                  </details>}
                  {clip.aiStatus === "processing" && <p role="status" style={{ color: "var(--muted, #64748b)" }}>Generating transcript and AI summary… this may take a few minutes.</p>}
                  {clip.aiStatus === "failed" && clip.aiError && <p role="alert" style={{ color: "#991b1b" }}>{clip.aiError}</p>}
                  {clip.allowAi && (!clip.summary || !clip.transcript) && (
                    <button className="btn-secondary" type="button" disabled={busy} onClick={() => void run(async () => {
                      try {
                        await api.post(`${path}/${clip.id}/summary`, undefined, { timeout: 360_000 });
                      } finally {
                        await load().catch(() => undefined);
                      }
                    })}>{clip.transcript ? "Retry AI summary" : clip.aiStatus === "failed" ? "Retry transcript and AI summary" : "Generate transcript and AI summary"}</button>
                  )}
                  {clip.kind === "progress" && !clip.allowAi && <p style={{ color: "var(--muted, #64748b)", fontSize: 13 }}>The parent did not opt in to AI processing for this video.</p>}
                  <label style={{ display: "block", marginTop: 8 }}>Therapist feedback
                    <textarea className="glass-input" maxLength={3000} style={{ display: "block", width: "100%" }}
                      value={feedback[clip.id] ?? clip.feedback ?? ""} disabled={busy}
                      onChange={e => setFeedback(prev => ({ ...prev, [clip.id]: e.target.value }))} />
                  </label>
                  <button className="btn-secondary" type="button" disabled={busy || !(feedback[clip.id] ?? "").trim()}
                    onClick={() => void run(async () => {
                      await api.put(`${path}/${clip.id}/feedback`, { text: feedback[clip.id] });
                      await load();
                    })}>Save feedback</button>
                </div>
              )}
              </div>
              <div style={{ minWidth: 0 }}>
                {videoUrls[clip.id] ? <video key={videoUrls[clip.id]} src={videoUrls[clip.id]} controls playsInline preload="metadata"
                  aria-label={`${clip.kind === "progress" ? "Progress clip" : "Therapist demonstration"} video`} style={{ display: "block", width: "100%", maxHeight: 300, borderRadius: 10, background: "#111827" }} />
                  : <div style={{ display: "grid", placeItems: "center", minHeight: 160, borderRadius: 10, background: "#eef1f6", color: "var(--muted, #64748b)", fontSize: 13 }}>{loaded ? "Preparing video…" : "Loading video…"}</div>}
              </div>
            </article>
          ))}
          <style jsx>{`@media (max-width: 720px) { article { grid-template-columns: 1fr !important; } }`}</style>
    </section>
  );
}
