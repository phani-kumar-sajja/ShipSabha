import type { AgentEvent, ResearchSession, StageStatus } from "../types/research";
import { STAGE_LABELS, STAGE_ORDER } from "../types/research";

function statusGlyph(status: StageStatus): { glyph: string; color: string } {
  switch (status) {
    case "complete":
      return { glyph: "✓", color: "var(--teal)" };
    case "running":
      return { glyph: "→", color: "var(--amber)" };
    case "failed":
      return { glyph: "✕", color: "var(--red)" };
    case "skipped":
      return { glyph: "·", color: "var(--text-muted)" };
    default:
      return { glyph: "○", color: "var(--text-muted)" };
  }
}

export function ProgressTracker({ session, events, connected }: { session: ResearchSession | null; events: AgentEvent[]; connected: boolean }) {
  if (!session) {
    return <div style={{ color: "var(--text-muted)" }}>Start a research session to see live progress here.</div>;
  }

  const stageByName = new Map(session.stages.map((s) => [s.stage, s]));

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <span
          style={{
            width: 8,
            height: 8,
            borderRadius: "50%",
            background: connected ? "var(--teal)" : "var(--text-muted)",
            display: "inline-block",
          }}
        />
        <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
          {connected ? "Live" : "Disconnected"} · Session <span className="mono">{session.session_id}</span>
        </span>
      </div>

      <div>
        {STAGE_ORDER.map((stage, i) => {
          const record = stageByName.get(stage);
          const status = record?.status ?? "pending";
          const { glyph, color } = statusGlyph(status);
          return (
            <div key={stage} style={{ display: "flex", gap: 12, padding: "6px 0" }}>
              <div style={{ width: 18, textAlign: "center", color, fontWeight: 700 }}>{glyph}</div>
              <div style={{ flex: 1 }}>
                <div style={{ color: status === "pending" ? "var(--text-muted)" : "var(--text)" }}>
                  {i + 1}. {STAGE_LABELS[stage]}
                </div>
                {record?.message && <div style={{ fontSize: 12, color: "var(--text-muted)" }}>{record.message}</div>}
                {record?.error && <div style={{ fontSize: 12, color: "var(--red)" }}>{record.error}</div>}
              </div>
            </div>
          );
        })}
      </div>

      <div>
        <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 6 }}>Activity log</div>
        <div
          className="mono"
          style={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: "var(--radius)",
            padding: 10,
            maxHeight: 220,
            overflowY: "auto",
            fontSize: 12,
          }}
        >
          {events.length === 0 && <div style={{ color: "var(--text-muted)" }}>No events yet.</div>}
          {events.map((event, i) => (
            <div key={i} style={{ padding: "2px 0", color: event.type.includes("error") || event.type.includes("rejected") ? "var(--red)" : "var(--text)" }}>
              <span style={{ color: "var(--text-muted)" }}>{new Date(event.timestamp).toLocaleTimeString()}</span> [{event.type}] {event.message}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
