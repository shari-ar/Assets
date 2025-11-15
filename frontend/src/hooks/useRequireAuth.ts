"use client";

import { useEffect, useMemo, useRef } from "react";
import { useRouter } from "next/navigation";
import { useShallow } from "zustand/react/shallow";

import { useAuthStore } from "@/hooks/useAuth";
import type { AuthUser } from "@/types/auth";

interface RequireAuthOptions {
  roles?: Array<AuthUser["role"]>;
  redirectTo?: string;
}

export function useRequireAuth({ roles, redirectTo = "/auth/login" }: RequireAuthOptions = {}) {
  const router = useRouter();
  const { user, initialized } = useAuthStore(
    useShallow((state) => ({
      user: state.user,
      initialized: state.initialized,
    })),
  );
  const lastRedirectRef = useRef<string | null>(null);

  const rolesKey = useMemo(() => (roles ? [...roles].sort().join("|") : ""), [roles]);
  const normalizedRoles = useMemo(
    () => (rolesKey ? (rolesKey.split("|") as Array<AuthUser["role"]>) : []),
    [rolesKey],
  );

  useEffect(() => {
    if (!initialized) {
      return;
    }

    if (!user) {
      if (lastRedirectRef.current !== redirectTo) {
        lastRedirectRef.current = redirectTo;
        router.replace(redirectTo);
      }
      return;
    }

    if (normalizedRoles.length > 0 && !normalizedRoles.includes(user.role)) {
      if (lastRedirectRef.current !== "/dashboard") {
        lastRedirectRef.current = "/dashboard";
        router.replace("/dashboard");
      }
      return;
    }

    lastRedirectRef.current = null;
  }, [initialized, normalizedRoles, redirectTo, router, user]);

  const isAuthorized = Boolean(
    user && (normalizedRoles.length === 0 || normalizedRoles.includes(user.role)),
  );

  return { user, initialized, isAuthorized };
}
