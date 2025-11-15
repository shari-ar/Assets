import { create } from "zustand";

import type { AuthUser } from "@/types/auth";

interface AuthState {
  user: AuthUser | null;
  initialized: boolean;
  setUser: (user: AuthUser | null) => void;
  clearUser: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  initialized: false,
  setUser: (user) =>
    set(() => ({
      user,
      initialized: true,
    })),
  clearUser: () =>
    set((state) =>
      state.user === null && state.initialized
        ? state
        : { user: null, initialized: true },
    ),
}));
