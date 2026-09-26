import { FormEvent, useState } from "react";
import type { CSSProperties } from "react";
import type { ResearchQuestionInput } from "../types/research";

interface Props {
  onSubmit: (input: ResearchQuestionInput) => void;
  submitting: boolean;
}

function splitLines(value: string): string[] {
  return value
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
}

export function ResearchQuestionForm({ onSubmit, submitting }: Props) {
  const [question, setQuestion] = useState("");
  const [constraints, setConstraints] = useState("");
  const [objectives, setObjectives] = useState("");
  const [datasets, setDatasets] = useState("");
  const [language, setLanguage] = useState("");
  const [computeConstraints, setComputeConstraints] = useState("");

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (question.trim().length < 8) return;
    onSubmit({
      research_question: question.trim(),
      constraints: splitLines(constraints),
      research_objectives: splitLines(objectives),
      datasets: splitLines(datasets),
      preferred_language: language.trim() || null,
      computational_constraints: computeConstraints.trim() || null,
    });
  }

  return (
    <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      <div>
        <label style={labelStyle}>Research question</label>
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="e.g. Does replacing attention with a state-space layer preserve long-context retrieval accuracy at lower FLOPs?"
          rows={4}
          style={{ width: "100%", resize: "vertical" }}
          className="mono"
          required
        />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
        <div>
          <label style={labelStyle}>Research objectives (one per line, optional)</label>
          <textarea value={objectives} onChange={(e) => setObjectives(e.target.value)} rows={3} style={{ width: "100%" }} />
        </div>
        <div>
          <label style={labelStyle}>Constraints (one per line, optional)</label>
          <textarea value={constraints} onChange={(e) => setConstraints(e.target.value)} rows={3} style={{ width: "100%" }} />
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
        <div>
          <label style={labelStyle}>Datasets (one per line, optional)</label>
          <textarea value={datasets} onChange={(e) => setDatasets(e.target.value)} rows={2} style={{ width: "100%" }} />
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <div>
            <label style={labelStyle}>Preferred language (optional)</label>
            <input value={language} onChange={(e) => setLanguage(e.target.value)} placeholder="Python" style={{ width: "100%" }} />
          </div>
          <div>
            <label style={labelStyle}>Compute constraints (optional)</label>
            <input
              value={computeConstraints}
              onChange={(e) => setComputeConstraints(e.target.value)}
              placeholder="Single GPU, 16GB VRAM"
              style={{ width: "100%" }}
            />
          </div>
        </div>
      </div>

      <button
        type="submit"
        disabled={submitting || question.trim().length < 8}
        style={{
          alignSelf: "flex-start",
          background: submitting ? "var(--border)" : "var(--indigo)",
          color: "#081019",
          fontWeight: 600,
          border: "none",
          borderRadius: "var(--radius)",
          padding: "10px 18px",
          cursor: submitting ? "default" : "pointer",
        }}
      >
        {submitting ? "Validating scope..." : "Start research"}
      </button>
    </form>
  );
}

const labelStyle: CSSProperties = {
  display: "block",
  fontSize: 12,
  color: "var(--text-muted)",
  marginBottom: 6,
};
