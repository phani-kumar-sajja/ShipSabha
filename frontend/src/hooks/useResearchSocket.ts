import { useEffect, useRef, useState } from "react";
import type { AgentEvent, ResearchSession, WsMessage } from "../types/research";

interface UseResearchSocketResult {
  session: ResearchSession | null;
  events: AgentEvent[];
  connected: boolean;
}

/**
 * Subscribes to /ws/sessions/{id} and keeps a live ResearchSession plus a
 * running event log in sync, without ever blocking the rest of the UI
 * (Section 19: responsiveness during long-running stages).
 */
export function useResearchSocket(sessionId: string | null): UseResearchSocketResult {
  const [session, setSession] = useState<ResearchSession | null>(null);
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!sessionId) return;

    setEvents([]);
    setSession(null);

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const socket = new WebSocket(`${protocol}//${window.location.host}/ws/sessions/${sessionId}`);
    socketRef.current = socket;

    socket.onopen = () => setConnected(true);
    socket.onclose = () => setConnected(false);
    socket.onerror = () => setConnected(false);

    socket.onmessage = (raw) => {
      const msg = JSON.parse(raw.data) as WsMessage;
      if (msg.type === "snapshot") {
        setSession(msg.session);
        return;
      }
      if (msg.type === "error") {
        return;
      }
      const event = msg as AgentEvent;
      setEvents((prev) => [...prev, event]);
      // Re-fetch full session snapshot on any stage-affecting event so the
      // stage list / status badges reflect the authoritative server state
      // rather than us reconstructing it client-side.
      fetch(`/api/sessions/${sessionId}`)
        .then((res) => res.json())
        .then(setSession)
        .catch(() => undefined);
    };

    return () => {
      socket.close();
      socketRef.current = null;
    };
  }, [sessionId]);

  return { session, events, connected };
}
