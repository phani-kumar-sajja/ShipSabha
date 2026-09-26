import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useResearchSocket } from "../hooks/useResearchSocket";
import type { ResearchQuestionInput, ResearchSession } from "../types/research";
import { ResearchQuestionForm } from "./ResearchQuestionForm";
import { ProgressTracker } from "./ProgressTracker";
import { DomainRejection } from "./DomainRejection";

export function ResearchDashboard() {
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [history, setHistory] = useState<ResearchSession[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const { session, events, connected } = useResearchSocket(activeSessionId);

  useEffect(() => {
    api.listSessions().then(setHistory).catch(() => undefined);
  }, [session?.status]);

  async function handleSubmit(input: ResearchQuestionInput) {
    setSubmitting(true);
    setSubmitError(null);
    try {
      const created = await api.createSession(input);
      setActiveSessionId(created.session_id);
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : "Failed to start session.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div style={{ display: "grid", gridTemplateColumns: "300px 1fr 380px", minHeight: "100vh" }}>
      {/* Left rail: session history */}
      <aside style={{ borderRight: "1px solid var(--border)", padding: "20px 16px", overflowY: "auto" }}>
        <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 10, letterSpacing: 0.2 }}>Sessions</div>
        <button
          onClick={() => setActiveSessionId(null)}
          style={{
            width: "100%",
            textAlign: "left",
            background: "transparent",
            border: "1px dashed var(--border)",
            color: "var(--indigo)",
            borderRadius: "var(--radius)",
            padding: "8px 10px",
            marginBottom: 12,
            cursor: "pointer",
          }}
        >
          + New research question
        </button>
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          {history.map((s) => (
            <button
              key={s.session_id}
              onClick={() => setActiveSessionId(s.session_id)}
              style={{
                textAlign: "left",
                background: s.session_id === activeSessionId ? "var(--surface-raised)" : "transparent",
                border: "1px solid var(--border)",
                borderRadius: "var(--radius)",
                padding: "8px 10px",
                color: "var(--text)",
                cursor: "pointer",
                fontSize: 12,
              }}
            >
              <div style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{s.research_question}</div>
              <div style={{ color: "var(--text-muted)", marginTop: 2 }}>{s.status}</div>
            </button>
          ))}
          {history.length === 0 && <div style={{ color: "var(--text-muted)", fontSize: 12 }}>No sessions yet.</div>}
        </div>
      </aside>

      {/* Center: intake or read-only summary of the active question */}
      <main style={{ padding: "20px 28px", overflowY: "auto" }}>
        <header style={{ marginBottom: 24 }}>
          <h1 style={{ fontSize: 20, fontWeight: 700, margin: 0 }}>Agentic CSE Research Assistant</h1>
          <p style={{ color: "var(--text-muted)", margin: "4px 0 0" }}>
            Enter a Computer Science &amp; Engineering research question to start an end-to-end research workflow.
          </p>
        </header>

        {!activeSessionId && (
          <ResearchQuestionForm onSubmit={handleSubmit} submitting={submitting} />
        )}

        {submitError && (
          <div style={{ marginTop: 12, color: "var(--red)", fontSize: 13 }}>{submitError}</div>
        )}

        {activeSessionId && session && (
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            <div>
              <div style={{ fontSize: 12, color: "var(--text-muted)" }}>Research question</div>
              <div className="mono" style={{ marginTop: 4 }}>{session.research_question}</div>
            </div>
            {session.domain && (
              <div style={{ fontSize: 13 }}>
                Domain: <strong>{session.domain}</strong>
                {session.subdomain ? ` / ${session.subdomain}` : ""}
              </div>
            )}
            {session.status === "rejected" && session.domain_validation && (
              <DomainRejection result={session.domain_validation} />
            )}
            {session.status === "error" && (
              <div style={{ color: "var(--red)" }}>
                Domain validation failed unexpectedly. Check the activity log on the right and the backend logs.
              </div>
            )}
          </div>
        )}
      </main>

      {/* Right: live progress */}
      <aside style={{ borderLeft: "1px solid var(--border)", padding: "20px 16px", overflowY: "auto" }}>
        <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 10 }}>Research progress</div>
        <ProgressTracker session={session} events={events} connected={connected} />
      </aside>
    </div>
  );
}
