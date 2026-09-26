import type { DomainValidationResult } from "../types/research";

export function DomainRejection({ result }: { result: DomainValidationResult }) {
  return (
    <div
      style={{
        border: "1px solid var(--red)",
        background: "rgba(232,99,107,0.08)",
        borderRadius: "var(--radius)",
        padding: 16,
      }}
    >
      <div style={{ fontWeight: 600, marginBottom: 6 }}>Outside CSE scope</div>
      <p style={{ margin: "0 0 8px", color: "var(--text-muted)" }}>
        This assistant only runs research workflows for Computer Science and Engineering questions. {result.rationale}
      </p>
      {result.suggested_reformulation && (
        <p style={{ margin: 0 }}>
          Consider reframing it as: <span className="mono">{result.suggested_reformulation}</span>
        </p>
      )}
    </div>
  );
}
