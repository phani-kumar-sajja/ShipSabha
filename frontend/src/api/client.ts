import type { ResearchQuestionInput, ResearchSession } from "../types/research";

const BASE = "/api";

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed with status ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  createSession(input: ResearchQuestionInput): Promise<ResearchSession> {
    return fetch(`${BASE}/sessions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input),
    }).then((res) => handle<ResearchSession>(res));
  },

  getSession(sessionId: string): Promise<ResearchSession> {
    return fetch(`${BASE}/sessions/${sessionId}`).then((res) => handle<ResearchSession>(res));
  },

  listSessions(): Promise<ResearchSession[]> {
    return fetch(`${BASE}/sessions`).then((res) => handle<ResearchSession[]>(res));
  },

  deleteSession(sessionId: string): Promise<void> {
    return fetch(`${BASE}/sessions/${sessionId}`, { method: "DELETE" }).then((res) => {
      if (!res.ok) throw new Error(`Failed to delete session ${sessionId}`);
    });
  },
};
