import { useEffect } from "react";
import { fetchSessions, deleteSession } from "../api/client";
import { useAppStore } from "../store/appStore";

export function useSessions() {
  const { setSessions, removeSession, setActiveSession, activeSessionId } = useAppStore();

  useEffect(() => {
    fetchSessions()
      .then(setSessions)
      .catch((err) => console.error("[useSessions] Failed to load sessions:", err));
  }, []);

  async function handleDelete(session_id: string) {
    try {
      await deleteSession(session_id);
      removeSession(session_id);
    } catch (err) {
      console.error("[useSessions] Delete failed:", err);
    }
  }

  return { handleDelete, setActiveSession, activeSessionId };
}
