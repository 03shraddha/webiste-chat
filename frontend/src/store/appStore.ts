import { create } from "zustand";
import type { Session, Message } from "../types";

interface AppStore {
  sessions: Session[];
  activeSessionId: string | null;
  messages: Record<string, Message[]>;

  setSessions: (sessions: Session[]) => void;
  addSession: (session: Session) => void;
  removeSession: (session_id: string) => void;
  setActiveSession: (session_id: string | null) => void;

  addMessage: (session_id: string, message: Message) => void;
  updateLastMessage: (session_id: string, patch: Partial<Message>) => void;
  getMessages: (session_id: string) => Message[];
}

export const useAppStore = create<AppStore>((set, get) => ({
  sessions: [],
  activeSessionId: null,
  messages: {},

  setSessions: (sessions) => set({ sessions }),

  addSession: (session) =>
    set((s) => ({
      sessions: [session, ...s.sessions.filter((x) => x.session_id !== session.session_id)],
    })),

  removeSession: (id) =>
    set((s) => ({
      sessions: s.sessions.filter((x) => x.session_id !== id),
      activeSessionId: s.activeSessionId === id ? null : s.activeSessionId,
    })),

  setActiveSession: (id) => set({ activeSessionId: id }),

  addMessage: (session_id, message) =>
    set((s) => ({
      messages: {
        ...s.messages,
        [session_id]: [...(s.messages[session_id] ?? []), message],
      },
    })),

  updateLastMessage: (session_id, patch) =>
    set((s) => {
      const msgs = [...(s.messages[session_id] ?? [])];
      if (msgs.length > 0) {
        msgs[msgs.length - 1] = { ...msgs[msgs.length - 1], ...patch };
      }
      return { messages: { ...s.messages, [session_id]: msgs } };
    }),

  getMessages: (session_id) => get().messages[session_id] ?? [],
}));
